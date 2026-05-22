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
import time

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
from pipecat.frames.frames import (
    LLMContextFrame,
    TranscriptionFrame,
    VADUserStartedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.tts_service import TextAggregationMode
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.audio.filters.rnnoise_filter import RNNoiseFilter
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import TurnAnalyzerUserTurnStopStrategy
from pipecat.turns.user_start.vad_user_turn_start_strategy import VADUserTurnStartStrategy
from pipecat.audio.vad.silero import SileroVADAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptTracker(FrameProcessor):
    """
    Passes frames through, but:
      - Drops TranscriptionFrames that arrive without a preceding VAD speech event
        (kills ElevenLabs STT hallucinations like "Thank you for watching" that
        come from ambient noise or speaker bleed).
      - Logs only the high-signal frames (final transcripts, VAD edges, turn events).
      - Updates memory.last_user_spoke_at on real transcripts.
    """

    # Only log these — drop the spammy ones like UserSpeakingFrame, BotSpeakingFrame,
    # InterimTranscriptionFrame.
    _LOG_FRAMES = (
        "TranscriptionFrame",
        "VADUserStartedSpeakingFrame",
        "VADUserStoppedSpeakingFrame",
        "UserStartedSpeakingFrame",
        "UserStoppedSpeakingFrame",
        "BotStartedSpeakingFrame",
        "BotStoppedSpeakingFrame",
    )

    def __init__(self, memory: MemoryStore):
        super().__init__()
        self._memory = memory
        self._vad_active = False
        # Allow transcripts to land for a short window AFTER VAD stopped, since the
        # final transcript usually arrives ~100-300ms after VAD says silence.
        self._last_vad_stop_at = 0.0

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        # Track VAD state for hallucination gating
        if isinstance(frame, VADUserStartedSpeakingFrame):
            self._vad_active = True
        elif isinstance(frame, VADUserStoppedSpeakingFrame):
            self._vad_active = False
            self._last_vad_stop_at = time.time()

        # Drop committed transcripts that arrive without VAD context
        if isinstance(frame, TranscriptionFrame):
            since_vad_stop = time.time() - self._last_vad_stop_at
            if not self._vad_active and since_vad_stop > 2.0:
                logger.warning(
                    f"[tracker] dropping hallucinated transcript "
                    f"(VAD never fired): {frame.text!r}"
                )
                return  # don't push downstream
            if frame.text.strip():
                self._memory.state.last_user_spoke_at = time.time()

        fname = type(frame).__name__
        if fname in self._LOG_FRAMES:
            text_preview = f" text={frame.text!r}" if hasattr(frame, "text") else ""
            logger.info(f"[tracker] {fname} dir={direction.name}{text_preview}")

        await self.push_frame(frame, direction)


async def main():
    memory = MemoryStore(state_path=STATE_PATH, max_turns=MEMORY_MAX_TURNS)
    tts_inject_queue: asyncio.Queue = asyncio.Queue()

    # --- Transport (mic + speakers) ---
    # NOTE: RNNoiseFilter disabled — was breaking SmartTurn end-of-turn detection.
    # Re-enable only if mic bleed becomes a problem again.
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        )
    )

    # --- STT (ElevenLabs Scribe v2 Realtime) ---
    stt = ElevenLabsRealtimeSTTService(api_key=ELEVENLABS_API_KEY)

    # --- LLM ---
    llm = AnthropicLLMService(
        api_key=ANTHROPIC_API_KEY,
        settings=AnthropicLLMService.Settings(
            model=CLAUDE_MODEL,
            system_instruction=build_system_prompt(memory),
            enable_prompt_caching=True,
        ),
    )

    # --- TTS ---
    tts = ElevenLabsTTSService(
        api_key=ELEVENLABS_API_KEY,
        settings=ElevenLabsTTSService.Settings(voice=ELEVENLABS_VOICE_ID),
        text_aggregation_mode=TextAggregationMode.TOKEN,
    )

    # --- Context + aggregators ---
    context = LLMContext(messages=memory.as_messages())
    turn_analyzer = LocalSmartTurnAnalyzerV3(params=SmartTurnParams(stop_secs=2.5))
    context_agg = LLMContextAggregatorPair(
        context=context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
            user_turn_strategies=UserTurnStrategies(
                # VAD-only — skip TranscriptionUserTurnStartStrategy so interim
                # transcript spam doesn't keep retriggering interruptions.
                # enable_interruptions=False so the bot can finish a sentence.
                start=[VADUserTurnStartStrategy(enable_interruptions=False)],
                stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=turn_analyzer)],
            ),
            user_turn_stop_timeout=4.0,
        ),
    )

    tracker = TranscriptTracker(memory)

    # --- Pipeline ---
    pipeline = Pipeline([
        transport.input(),
        stt,
        tracker,
        context_agg.user(),
        llm,
        tts,
        transport.output(),
        context_agg.assistant(),
    ])

    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=False))

    # --- Proactive loop ---
    proactive = ProactiveLoop(memory=memory, tts_queue=tts_inject_queue, context=context)

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
