"""
Listen Module - Speech Recognition and Audio Input
===================================================
Handles microphone input, audio processing, and speech-to-text conversion.
Supports both online (Google) and offline (Whisper) recognition options.

Key Features:
- Adaptive noise adjustment
- Multiple recognition backends
- Error handling and recovery
- Audio quality monitoring
- Background noise suppression
"""

from typing import Optional
import logging
import speech_recognition as sr
import config

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONAL: OFFLINE SPEECH RECOGNITION
# ============================================================================
# To enable offline/local transcription with faster_whisper:
# 1. Install: pip install faster-whisper
# 2. Uncomment the code below
# 3. Set USE_OFFLINE_RECOGNITION = True

USE_OFFLINE_RECOGNITION = False


# Uncomment these lines to enable offline recognition:
# try:
#     from faster_whisper import WhisperModel
#     USE_OFFLINE_RECOGNITION = True
#     logger.info("Offline speech recognition available")
# except ImportError:
#     USE_OFFLINE_RECOGNITION = False
#     logger.info("Using online speech recognition")

# ============================================================================
# LISTENER CLASS - SPEECH RECOGNITION
# ============================================================================
class Listener:
    """
    Speech recognition system for Jarvis voice input.

    This class handles:
    - Microphone audio capture
    - Ambient noise adjustment
    - Speech-to-text conversion
    - Error handling and recovery
    - Audio quality monitoring
    """

    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    def __init__(
            self,
            energy_threshold: Optional[int] = None,
            pause_threshold: float = 0.6,
            timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the speech recognition system.

        Args:
            energy_threshold: Minimum audio energy to consider as speech.
                            Higher = less sensitive to quiet sounds.
                            If None, uses config default or auto-adjusts.
            pause_threshold: Seconds of silence to mark end of speech.
                           Lower = faster but may cut off speech.
            timeout: Maximum time to wait for speech (None = no timeout)
        """
        # ====================================================================
        # STEP 1: Initialize speech recognizer
        # ====================================================================
        self.recognizer = sr.Recognizer()

        # Configure energy threshold for speech detection
        if energy_threshold:
            self.recognizer.energy_threshold = energy_threshold
        elif config.SPEECH_ENERGY_THRESHOLD:
            self.recognizer.energy_threshold = config.SPEECH_ENERGY_THRESHOLD
        # else: will auto-adjust during calibration

        # Configure pause detection
        self.recognizer.pause_threshold = pause_threshold
        self.timeout = timeout

        # Track calibration status
        self.is_calibrated = False

        # Statistics for monitoring
        self.total_attempts = 0
        self.successful_recognitions = 0
        self.failed_recognitions = 0

        logger.info("Listener initialized")
        logger.debug("Energy threshold: %s, Pause threshold: %s",
                     self.recognizer.energy_threshold, pause_threshold)

        # ====================================================================
        # STEP 2: Calibrate for ambient noise
        # ====================================================================
        self._calibrate_microphone()

    # ========================================================================
    # MICROPHONE CALIBRATION
    # ========================================================================
    def _calibrate_microphone(self) -> None:
        """
        Adjust for ambient noise to improve recognition accuracy.

        This one-time calibration helps filter out background noise
        and improves speech detection. Should be run in a quiet environment
        for best results.
        """
        try:
            logger.info("Calibrating microphone for ambient noise...")
            print("Calibrating microphone - please remain quiet for a moment...")

            with sr.Microphone() as source:
                # Listen to ambient noise and adjust threshold
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)

            self.is_calibrated = True
            logger.info("Calibration complete. Energy threshold: %d",
                        self.recognizer.energy_threshold)
            print(f"Calibration complete! Ready to listen.")

        except Exception as exc:
            logger.error("Calibration failed: %s", exc)
            print(f"Warning: Could not calibrate microphone: {exc}")
            print("Speech recognition may be less accurate.")

    def recalibrate(self) -> bool:
        """
        Recalibrate the microphone for changed environment conditions.

        Call this if you move to a different room or if background
        noise levels have changed significantly.

        Returns:
            True if calibration succeeded, False otherwise
        """
        try:
            self._calibrate_microphone()
            return True
        except Exception as exc:
            logger.error("Recalibration failed: %s", exc)
            return False

    # ========================================================================
    # SPEECH RECOGNITION - ONLINE MODE
    # ========================================================================
    def _recognize_online(self, audio: sr.AudioData) -> Optional[str]:
        """
        Transcribe audio using Google's online speech recognition.

        Requires internet connection but generally more accurate for
        diverse accents and languages.

        Args:
            audio: Recorded audio data to transcribe

        Returns:
            Transcribed text or None if recognition failed
        """
        try:
            text = self.recognizer.recognize_google(audio)
            logger.debug("Online recognition successful: '%s'", text)
            return text

        except sr.UnknownValueError:
            # Speech was unintelligible
            logger.debug("Online recognition: Speech unclear")
            return None

        except sr.RequestError as exc:
            # Network or service error
            error_msg = str(exc).lower()

            # Check for common connection issues
            if any(keyword in error_msg for keyword in
                   ["network", "connection", "internet", "timeout"]):
                logger.error("Network error during recognition: %s", exc)
                return "Connection error: Please check your internet connection."

            # Other service errors
            logger.error("Speech recognition service error: %s", exc)
            return f"Speech recognition service error: {exc}"

    # ========================================================================
    # SPEECH RECOGNITION - OFFLINE MODE
    # ========================================================================
    def _recognize_offline(self, audio: sr.AudioData) -> Optional[str]:
        """
        Transcribe audio using local Whisper model (offline).

        Requires faster_whisper installation. Works without internet
        but may be slower and require more system resources.

        Args:
            audio: Recorded audio data to transcribe

        Returns:
            Transcribed text or None if recognition failed
        """
        if not USE_OFFLINE_RECOGNITION:
            return self._recognize_online(audio)

        try:
            # This would be implemented if faster_whisper is installed
            # model = WhisperModel("base", device="cpu", compute_type="int8")
            # segments, info = model.transcribe(audio, language="en")
            # text = " ".join([segment.text for segment in segments])
            # return text

            logger.warning("Offline recognition not fully implemented")
            return self._recognize_online(audio)

        except Exception as exc:
            logger.error("Offline recognition error: %s", exc)
            return None

    # ========================================================================
    # MAIN LISTENING INTERFACE
    # ========================================================================
    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Capture and transcribe speech from the microphone.

        This is the main interface for getting voice input. It will:
        1. Wait for speech to begin
        2. Record until silence is detected
        3. Transcribe the audio to text
        4. Return the result

        Args:
            timeout: Maximum seconds to wait for speech. None = use default.

        Returns:
            Transcribed text string, or None if no speech detected,
            or error message string if recognition failed
        """
        self.total_attempts += 1

        try:
            # ================================================================
            # STEP 1: Capture audio from microphone
            # ================================================================
            with sr.Microphone() as source:
                logger.debug("Listening for speech...")

                # Wait for and record speech
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout or self.timeout,
                    phrase_time_limit=config.SPEECH_PHRASE_TIME_LIMIT
                )

                logger.debug("Audio captured, processing...")

            # ================================================================
            # STEP 2: Transcribe audio to text
            # ================================================================
            # Choose recognition method based on configuration
            if USE_OFFLINE_RECOGNITION:
                text = self._recognize_offline(audio)
            else:
                text = self._recognize_online(audio)

            # ================================================================
            # STEP 3: Process and return result
            # ================================================================
            if text:
                self.successful_recognitions += 1
                logger.info("Recognition success: '%s'", text)
            else:
                self.failed_recognitions += 1

            return text

        except sr.WaitTimeoutError:
            # ================================================================
            # HANDLE TIMEOUT (no speech detected)
            # ================================================================
            logger.debug("Listen timeout - no speech detected")
            return None

        except Exception as exc:
            # ================================================================
            # HANDLE MICROPHONE OR SYSTEM ERRORS
            # ================================================================
            logger.exception("Microphone error")
            self.failed_recognitions += 1
            return f"Microphone error: {exc}"

    # ========================================================================
    # QUICK LISTEN (with default timeout)
    # ========================================================================
    def quick_listen(self, timeout: float = 3.0) -> Optional[str]:
        """
        Quick listen with short timeout for fast interactions.

        Useful for simple yes/no questions or quick commands.

        Args:
            timeout: Maximum seconds to wait (default 3 seconds)

        Returns:
            Transcribed text or None
        """
        return self.listen(timeout=timeout)

    # ========================================================================
    # CONTINUOUS LISTENING
    # ========================================================================
    def listen_continuous(self, callback, stop_phrase: str = "stop listening"):
        """
        Continuously listen and process speech until stop phrase heard.

        EXPERIMENTAL: For continuous conversation mode.

        Args:
            callback: Function to call with each transcribed phrase
            stop_phrase: Phrase that stops continuous listening
        """
        logger.info("Starting continuous listening mode")
        print(f"Continuous listening active. Say '{stop_phrase}' to stop.")

        while True:
            text = self.listen()

            if not text:
                continue

            if stop_phrase.lower() in text.lower():
                logger.info("Stop phrase detected, ending continuous mode")
                break

            callback(text)

    # ========================================================================
    # STATISTICS AND MONITORING
    # ========================================================================
    def get_stats(self) -> dict:
        """
        Get speech recognition statistics.

        Returns:
            Dictionary with recognition performance metrics
        """
        success_rate = (
            (self.successful_recognitions / self.total_attempts * 100)
            if self.total_attempts > 0 else 0
        )

        return {
            "total_attempts": self.total_attempts,
            "successful": self.successful_recognitions,
            "failed": self.failed_recognitions,
            "success_rate": f"{success_rate:.1f}%",
            "calibrated": self.is_calibrated,
            "energy_threshold": self.recognizer.energy_threshold,
            "recognition_mode": "offline" if USE_OFFLINE_RECOGNITION else "online"
        }

    def print_stats(self) -> None:
        """Print recognition statistics to console."""
        stats = self.get_stats()
        print("\n=== Listener Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("===========================\n")

    # ========================================================================
    # CONFIGURATION ADJUSTMENTS
    # ========================================================================
    def adjust_sensitivity(self, increase: bool = True) -> None:
        """
        Adjust microphone sensitivity up or down.

        Args:
            increase: True to make more sensitive (lower threshold),
                     False to make less sensitive (higher threshold)
        """
        adjustment = -100 if increase else 100
        self.recognizer.energy_threshold += adjustment

        logger.info("Sensitivity adjusted. New threshold: %d",
                    self.recognizer.energy_threshold)
        print(f"Microphone sensitivity {'increased' if increase else 'decreased'}")