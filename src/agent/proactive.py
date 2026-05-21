import asyncio
import logging
from config.settings import SILENCE_LIGHT, SILENCE_MEDIUM, SILENCE_LONG
from cgshared.memory.store import MemoryStore
from topics.engine import generate_interjection

logger = logging.getLogger(__name__)


class ProactiveLoop:
    """
    Background loop that monitors silence and fires unprompted speech
    by injecting text into the Pipecat pipeline's TTS input queue.
    """

    def __init__(self, memory: MemoryStore, tts_queue: asyncio.Queue):
        self.memory = memory
        self.tts_queue = tts_queue
        self._running = False
        self._last_interjection_at = 0.0

    async def run(self):
        self._running = True
        import time

        while self._running:
            await asyncio.sleep(10)  # check every 10s

            silence = self.memory.seconds_since_user_spoke()
            cooldown = time.time() - self._last_interjection_at

            # don't interject twice in under 90s regardless of threshold
            if cooldown < 90:
                continue

            if silence >= SILENCE_LIGHT:
                try:
                    text = generate_interjection(self.memory, silence)
                    logger.info(f"[proactive] injecting after {silence:.0f}s silence: {text!r}")
                    await self.tts_queue.put(text)
                    self.memory.add_turn("assistant", text)
                    import time as _t
                    self._last_interjection_at = _t.time()
                except Exception as e:
                    logger.error(f"[proactive] interjection failed: {e}")

    def stop(self):
        self._running = False
