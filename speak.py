"""
Speak Module - Text-to-Speech Output
====================================
Handles all voice output using pyttsx3 text-to-speech engine.
Provides non-blocking speech with queue management and voice control.

Key Features:
- Non-blocking threaded speech
- Speech queue management
- Voice customization (rate, volume, voice)
- Interrupt and stop controls
- Speech progress monitoring
"""

from typing import Optional, List
import threading
import logging
import queue
import time
import pyttsx3
import config

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# SPEAKER CLASS - TEXT-TO-SPEECH SYSTEM
# ============================================================================
class Speaker:
    """
    Text-to-speech system for Jarvis voice output.

    This class handles:
    - Converting text to spoken audio
    - Managing speech queue
    - Non-blocking operation
    - Voice customization
    - Speech interruption and control
    """

    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    def __init__(
            self,
            rate: Optional[int] = None,
            volume: Optional[float] = None,
            voice_id: Optional[str] = None
    ) -> None:
        """
        Initialize the text-to-speech engine.

        Args:
            rate: Speaking rate in words per minute (100-300 typical).
                 Higher = faster speech. If None, uses config default.
            volume: Volume level from 0.0 (silent) to 1.0 (maximum).
                   If None, uses config default.
            voice_id: Specific voice ID to use. If None, uses system default.
        """
        # ====================================================================
        # STEP 1: Initialize TTS engine
        # ====================================================================
        try:
            self.engine = pyttsx3.init()
            logger.info("TTS engine initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize TTS engine: %s", exc)
            raise RuntimeError(f"Cannot initialize speech engine: {exc}")

        # ====================================================================
        # STEP 2: Configure voice properties
        # ====================================================================
        # Set speaking rate
        if rate is not None:
            self.engine.setProperty("rate", rate)
        elif config.DEFAULT_VOICE_RATE:
            self.engine.setProperty("rate", config.DEFAULT_VOICE_RATE)

        # Set volume
        if volume is not None:
            self.engine.setProperty("volume", volume)
        elif config.DEFAULT_VOICE_VOLUME:
            self.engine.setProperty("volume", config.DEFAULT_VOICE_VOLUME)

        # Set specific voice if requested
        if voice_id:
            self.set_voice(voice_id)

        # ====================================================================
        # STEP 3: Initialize state tracking
        # ====================================================================
        self._speaking = threading.Event()  # Tracks if currently speaking
        self._speech_queue = queue.Queue()  # Queue for pending speech
        self._queue_thread: Optional[threading.Thread] = None
        self._queue_active = False
        self._current_text: Optional[str] = None

        # Statistics
        self.total_utterances = 0
        self.total_characters = 0

        # Log configuration
        current_rate = self.engine.getProperty("rate")
        current_volume = self.engine.getProperty("volume")
        logger.info("Speaker configured - Rate: %d, Volume: %.2f",
                    current_rate, current_volume)

    # ========================================================================
    # VOICE SELECTION AND CUSTOMIZATION
    # ========================================================================
    def get_available_voices(self) -> List[dict]:
        """
        Get list of available voices on the system.

        Returns:
            List of voice dictionaries with id, name, and languages
        """
        voices = self.engine.getProperty("voices")
        voice_list = []

        for voice in voices:
            voice_info = {
                "id": voice.id,
                "name": voice.name,
                "languages": voice.languages,
                "gender": getattr(voice, "gender", "unknown")
            }
            voice_list.append(voice_info)

        return voice_list

    def set_voice(self, voice_id: str) -> bool:
        """
        Change the voice used for speech.

        Args:
            voice_id: Voice ID from get_available_voices()

        Returns:
            True if voice was set successfully, False otherwise
        """
        try:
            self.engine.setProperty("voice", voice_id)
            logger.info("Voice changed to: %s", voice_id)
            return True
        except Exception as exc:
            logger.error("Failed to set voice: %s", exc)
            return False

    def print_available_voices(self) -> None:
        """Print all available voices to console."""
        voices = self.get_available_voices()
        print("\n=== Available Voices ===")
        for i, voice in enumerate(voices, 1):
            print(f"{i}. {voice['name']}")
            print(f"   ID: {voice['id']}")
            print(f"   Languages: {voice['languages']}")
            print()

    def adjust_rate(self, change: int) -> None:
        """
        Adjust speaking rate by specified amount.

        Args:
            change: Amount to increase (positive) or decrease (negative)
        """
        current_rate = self.engine.getProperty("rate")
        new_rate = max(50, min(300, current_rate + change))  # Clamp 50-300
        self.engine.setProperty("rate", new_rate)
        logger.info("Speaking rate adjusted: %d -> %d", current_rate, new_rate)

    def adjust_volume(self, change: float) -> None:
        """
        Adjust volume by specified amount.

        Args:
            change: Amount to increase (positive) or decrease (negative)
        """
        current_volume = self.engine.getProperty("volume")
        new_volume = max(0.0, min(1.0, current_volume + change))  # Clamp 0-1
        self.engine.setProperty("volume", new_volume)
        logger.info("Volume adjusted: %.2f -> %.2f", current_volume, new_volume)

    # ========================================================================
    # SPEECH EXECUTION - INTERNAL THREAD
    # ========================================================================
    def _say_thread(self, text: str) -> None:
        """
        Internal method that performs the actual TTS operation.

        Runs in a separate thread to avoid blocking the main program.
        Handles speech execution and state management.

        Args:
            text: Text to speak aloud
        """
        try:
            # Mark as speaking
            self._speaking.set()
            self._current_text = text

            logger.debug("Speaking: '%s'", text[:50] + "..." if len(text) > 50 else text)

            # Perform text-to-speech
            self.engine.say(text)
            self.engine.runAndWait()

            # Update statistics
            self.total_utterances += 1
            self.total_characters += len(text)

            logger.debug("Speech completed")

        except Exception as exc:
            # Don't crash on TTS errors, just log them
            logger.error("TTS error: %s", exc)

        finally:
            # Clear speaking state
            self._speaking.clear()
            self._current_text = None

    # ========================================================================
    # BASIC SPEECH INTERFACE
    # ========================================================================
    def say(self, text: str, block: bool = False) -> None:
        """
        Speak the provided text aloud.

        This is the main interface for speech output. By default, it's
        non-blocking - the function returns immediately while speech
        continues in the background.

        Args:
            text: Text to speak
            block: If True, wait for speech to complete before returning
        """
        if not text or not text.strip():
            logger.warning("Attempted to speak empty text")
            return

        # Clean up text for better speech
        text = text.strip()

        # Create and start speech thread
        thread = threading.Thread(
            target=self._say_thread,
            args=(text,),
            daemon=True,
            name="SpeechThread"
        )
        thread.start()

        # Wait for completion if blocking requested
        if block:
            thread.join()

    def say_immediately(self, text: str) -> None:
        """
        Stop any current speech and speak new text immediately.

        Interrupts current speech and clears queue to speak urgent message.

        Args:
            text: Urgent text to speak
        """
        self.stop()
        self.clear_queue()
        self.say(text, block=False)

    # ========================================================================
    # SPEECH QUEUE MANAGEMENT
    # ========================================================================
    def say_queued(self, text: str) -> None:
        """
        Add text to speech queue for sequential speaking.

        Useful for speaking multiple messages without interruption.
        Queue will be processed in order.

        Args:
            text: Text to add to queue
        """
        self._speech_queue.put(text)
        logger.debug("Added to speech queue: '%s'", text[:50])

        # Start queue processor if not already running
        if not self._queue_active:
            self._start_queue_processor()

    def _start_queue_processor(self) -> None:
        """Start the background thread that processes the speech queue."""
        if self._queue_thread and self._queue_thread.is_alive():
            return  # Already running

        self._queue_active = True
        self._queue_thread = threading.Thread(
            target=self._process_queue,
            daemon=True,
            name="QueueProcessor"
        )
        self._queue_thread.start()
        logger.info("Speech queue processor started")

    def _process_queue(self) -> None:
        """Process queued speech items sequentially."""
        while self._queue_active:
            try:
                # Get next item with timeout
                text = self._speech_queue.get(timeout=1.0)

                # Wait for any current speech to finish
                while self.is_speaking():
                    time.sleep(0.1)

                # Speak the queued text
                self.say(text, block=True)

                self._speech_queue.task_done()

            except queue.Empty:
                # No items in queue, continue waiting
                continue
            except Exception as exc:
                logger.error("Queue processor error: %s", exc)

    def clear_queue(self) -> int:
        """
        Clear all pending items from speech queue.

        Returns:
            Number of items cleared
        """
        count = 0
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
                count += 1
            except queue.Empty:
                break

        if count > 0:
            logger.info("Cleared %d items from speech queue", count)

        return count

    def stop_queue_processor(self) -> None:
        """Stop the background queue processor thread."""
        self._queue_active = False
        if self._queue_thread:
            self._queue_thread.join(timeout=2.0)
        logger.info("Speech queue processor stopped")

    # ========================================================================
    # SPEECH CONTROL
    # ========================================================================
    def stop(self) -> None:
        """
        Stop the current speech immediately.

        Interrupts any ongoing speech. Does not affect queued items.
        """
        try:
            self.engine.stop()
            self._speaking.clear()
            self._current_text = None
            logger.info("Speech stopped")
        except Exception as exc:
            logger.error("Error stopping speech: %s", exc)

    def is_speaking(self) -> bool:
        """
        Check if currently speaking.

        Returns:
            True if speech is in progress, False otherwise
        """
        return self._speaking.is_set()

    def wait_until_done(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for current speech to complete.

        Args:
            timeout: Maximum seconds to wait. None = wait indefinitely

        Returns:
            True if speech completed, False if timeout occurred
        """
        if not self.is_speaking():
            return True

        return self._speaking.wait(timeout=timeout)

    def get_current_text(self) -> Optional[str]:
        """
        Get the text currently being spoken.

        Returns:
            Current text or None if not speaking
        """
        return self._current_text

    # ========================================================================
    # STATISTICS AND MONITORING
    # ========================================================================
    def get_stats(self) -> dict:
        """
        Get speech statistics and current state.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_utterances": self.total_utterances,
            "total_characters": self.total_characters,
            "currently_speaking": self.is_speaking(),
            "queue_size": self._speech_queue.qsize(),
            "queue_active": self._queue_active,
            "current_rate": self.engine.getProperty("rate"),
            "current_volume": self.engine.getProperty("volume")
        }

    def print_stats(self) -> None:
        """Print speech statistics to console."""
        stats = self.get_stats()
        print("\n=== Speaker Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("==========================\n")

    # ========================================================================
    # CLEANUP
    # ========================================================================
    def shutdown(self) -> None:
        """
        Safely shutdown the speaker system.

        Stops all speech, clears queue, and releases resources.
        """
        logger.info("Shutting down speaker")
        self.stop()
        self.stop_queue_processor()
        self.clear_queue()

        try:
            # Some TTS engines need explicit cleanup
            if hasattr(self.engine, 'endLoop'):
                self.engine.endLoop()
        except Exception as exc:
            logger.debug("Engine cleanup note: %s", exc)

        logger.info("Speaker shutdown complete")