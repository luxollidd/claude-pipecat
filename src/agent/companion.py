"""
Main entry point. Wires together:
  - Pipecat 1.2 pipeline (mic → STT → LLM → TTS → speakers)
  - ProactiveLoop (background silence monitor → TTS injector)
  - MemoryStore (conversation history + session state)
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import (
    ANTHROPIC_API_KEY, ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID, CLAUDE_MODEL,
    STATE_PATH, MEMORY_MAX_TURNS,
)
from memory.context import build_system_prompt
from cgshared.memory.store import MemoryStore
from agent.proactive import ProactiveLoop

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.frames.frames import LLMContextFrame
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    memory = MemoryStore(state_path=STATE_PATH, max_turns=MEMORY_MAX_TURNS)
    tts_inject_queue: asyncio.Queue = asyncio.Queue()

    # --- Transport (mic + speakers) ---
    transport = LocalAudioTransport(
        LocalAudioTransportParams(audio_in_enabled=True, audio_out_enabled=True)
    )

    # --- STT (ElevenLabs Scribe v2 Realtime) ---
    stt = ElevenLabsRealtimeSTTService(api_key=ELEVENLABS_API_KEY)

    # --- LLM ---
    llm = AnthropicLLMService(
        api_key=ANTHROPIC_API_KEY,
        settings=AnthropicLLMService.Settings(
            model=CLAUDE_MODEL,
            system_instruction=build_system_prompt(memory),
        ),
    )

    # --- TTS ---
    tts = ElevenLabsTTSService(
        api_key=ELEVENLABS_API_KEY,
        settings=ElevenLabsTTSService.Settings(voice=ELEVENLABS_VOICE_ID),
    )

    # --- Context + aggregators ---
    context = LLMContext(messages=memory.as_messages())
    context_agg = LLMContextAggregatorPair(context=context)

    # --- Pipeline ---
    pipeline = Pipeline([
        transport.input(),
        stt,
        context_agg.user(),
        llm,
        tts,
        transport.output(),
        context_agg.assistant(),
    ])

    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

    # --- Proactive loop ---
    proactive = ProactiveLoop(memory=memory, tts_queue=tts_inject_queue)

    # Drain inject queue and push updated context frames into the pipeline
    async def inject_loop():
        while True:
            await tts_inject_queue.get()
            updated_context = LLMContext(messages=memory.as_messages())
            await task.queue_frames([LLMContextFrame(context=updated_context)])

    # Kick off conversation on start
    async def on_first_participant():
        logger.info("[companion] session started")
        await task.queue_frames([LLMContextFrame(context=context)])

    runner = PipelineRunner()

    await asyncio.gather(
        runner.run(task),
        proactive.run(),
        inject_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
