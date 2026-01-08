#!/usr/bin/env python3
"""
Main Loop for Jarvis Voice Assistant
"""

import sys
import time
import logging
from datetime import datetime
import config
from brain import Brain
from listen import Listener
from speak import Speaker
import skills

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JarvisAssistant:
    """Main Jarvis assistant orchestrator."""

    def __init__(self):
        """Initialize all subsystems."""
        logger.info("JARVIS ASSISTANT STARTING")

        if not config.validate_config():
            logger.error("Configuration validation failed")
            raise RuntimeError("Invalid configuration - check logs")

        logger.info("Initializing components...")
        self.brain = Brain()
        logger.info("[OK] Brain (AI) initialized")

        self.listener = Listener(
            energy_threshold=config.SPEECH_ENERGY_THRESHOLD,
            pause_threshold=config.SPEECH_PAUSE_THRESHOLD
        )
        logger.info("[OK] Listener (Speech Recognition) initialized")

        self.speaker = Speaker(
            rate=config.DEFAULT_VOICE_RATE,
            volume=config.DEFAULT_VOICE_VOLUME
        )
        logger.info("[OK] Speaker (Text-to-Speech) initialized")

        self.running = False
        self.start_time = None
        self.total_interactions = 0
        self.successful_commands = 0
        self.ai_responses = 0
        self.errors = 0

        logger.info("JARVIS INITIALIZATION COMPLETE")

    @staticmethod
    def is_wake_word(text):
        """Check if text contains any configured wake word."""
        if not text:
            return False
        lowered = text.lower()
        for wake_word in config.WAKE_WORDS:
            if wake_word in lowered:
                logger.debug("Wake word detected: %s", wake_word)
                return True
        return False

    @staticmethod
    def strip_wake_words(text):
        """Remove wake words from text to extract the actual command."""
        command = text.lower()
        for wake_word in config.WAKE_WORDS:
            command = command.replace(wake_word, "")
        return command.strip()

    def find_skill(self, text):
        """Find the best matching skill for the given text."""
        lowered = text.lower()
        best_match = None
        best_keyword = None
        best_length = 0

        for keyword, func in skills.SKILLS.items():
            if keyword in lowered and len(keyword) > best_length:
                best_match = func
                best_keyword = keyword
                best_length = len(keyword)

        if best_match:
            logger.debug("Matched skill: %s -> %s", best_keyword, best_match.__name__)

        return best_match, best_keyword

    def execute_skill(self, skill_func, command, keyword):
        """Execute a skill function with appropriate arguments."""
        logger.info("Executing skill: %s", skill_func.__name__)

        try:
            if skill_func in [skills.open_app, skills.close_app, skills.search_web]:
                args = command.replace(keyword, "", 1).strip().split()
                if args:
                    arg_text = " ".join(args)
                    result = skill_func(arg_text)
                else:
                    result = "Please specify what to open."

            elif skill_func is skills.control_hardware:
                args = command.replace(keyword, "", 1).strip().split()
                action = args[0] if args else "status"
                result = skill_func(action)

            else:
                result = skill_func()

            self.successful_commands += 1
            logger.info("Skill executed successfully: %s", skill_func.__name__)
            return result

        except Exception as exc:
            logger.exception("Unexpected error in skill execution")
            self.errors += 1
            return f"I encountered an unexpected error: {exc}"

    def process_with_ai(self, command):
        """Process command using AI when no skill matches."""
        logger.info("Processing with AI: %s", command[:50])

        try:
            response = self.brain.chat(command)
            self.ai_responses += 1
            logger.info("AI response generated successfully")
            return response

        except Exception as exc:
            logger.exception("AI processing error")
            self.errors += 1
            return f"I had trouble processing that: {exc}"

    def handle_special_commands(self, text):
        """Handle special system commands."""
        lowered = text.lower()

        if any(word in lowered for word in config.STOP_WORDS):
            self.speaker.stop()
            logger.info("Stop command received")
            print("[STOPPED] Stopped speaking")
            return True

        if "statistics" in lowered or "stats" in lowered:
            self.print_statistics()
            return True

        if "clear history" in lowered or "forget conversation" in lowered:
            try:
                self.brain.clear_history()
                self.speaker.say("Conversation history cleared.")
                print("[CLEARED] Conversation history cleared")
                return True
            except AttributeError:
                print("[CLEARED] Clear history not available")
                return True

        if "help" in lowered and "jarvis" in lowered:
            self.show_help()
            return True

        return False

    def run(self):
        """Main event loop for Jarvis assistant."""
        self.running = True
        self.start_time = datetime.now()

        print("\n" + "=" * 60)
        print("[JARVIS] JARVIS IS NOW LISTENING")
        print("=" * 60)
        print(f"Wake words: {', '.join(config.WAKE_WORDS)}")
        print(f"Model: {config.MODEL_NAME}")
        print("Say wake word + command to interact")
        print("Press Ctrl+C to exit")
        print("=" * 60 + "\n")

        self.speaker.say("Jarvis is online and ready.")
        logger.info("Main loop started")

        while self.running:
            try:
                if self.speaker.is_speaking():
                    time.sleep(0.1)
                    continue

                heard = self.listener.listen()

                if not heard:
                    continue

                logger.info("Heard: %s", heard)
                print(f"\n[HEARD] Heard: {heard}")

                if self.handle_special_commands(heard):
                    continue

                if not self.is_wake_word(heard):
                    logger.debug("No wake word detected, ignoring")
                    continue

                self.total_interactions += 1
                logger.info("Wake word detected - interaction #%d", self.total_interactions)

                command = self.strip_wake_words(heard)

                if not command:
                    logger.debug("Empty command after wake word removal")
                    continue

                logger.info("Processing command: %s", command)

                skill_func, matched_keyword = self.find_skill(command)

                if skill_func:
                    print(f"[SKILL] Executing skill: {skill_func.__name__}")
                    result = self.execute_skill(skill_func, command, matched_keyword)
                else:
                    print("[AI] Processing with AI...")
                    result = self.process_with_ai(command)

                logger.info("Response: %s", result[:100])
                print(f"[JARVIS] Jarvis: {result}")
                self.speaker.say(result)

                time.sleep(0.2)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                self.shutdown()
                break

            except Exception as exc:
                logger.exception("Unexpected error in main loop")
                self.errors += 1
                print(f"[ERROR] Error: {exc}")
                time.sleep(1)

    def print_statistics(self):
        """Print current session statistics."""
        uptime = datetime.now() - self.start_time if self.start_time else None

        print("\n" + "=" * 60)
        print("[STATS] JARVIS STATISTICS")
        print("=" * 60)

        if uptime:
            print(f"Uptime: {uptime}")

        print(f"Total Interactions: {self.total_interactions}")
        print(f"Skill Executions: {self.successful_commands}")
        print(f"AI Responses: {self.ai_responses}")
        print(f"Errors: {self.errors}")

        print("\n--- Component Stats ---")
        try:
            for key, value in self.listener.get_stats().items():
                print(f"Listener {key}: {value}")
        except AttributeError:
            print("Listener stats unavailable")

        try:
            for key, value in self.speaker.get_stats().items():
                print(f"Speaker {key}: {value}")
        except AttributeError:
            print("Speaker stats unavailable")

        try:
            for key, value in self.brain.get_stats().items():
                print(f"Brain {key}: {value}")
        except AttributeError:
            print("Brain stats unavailable")

        print("=" * 60 + "\n")

        summary = (f"I've handled {self.total_interactions} interactions, "
                   f"with {self.successful_commands} skill executions "
                   f"and {self.ai_responses} AI responses.")
        self.speaker.say(summary)

    def show_help(self):
        """Show available commands and features."""
        help_text = """
        Available Skills:
        - Open applications: 'open Chrome', 'launch Calculator'
        - Time and date: 'what time', 'what date'
        - Hardware control: 'turn on lights', 'hardware status'
        - System info: 'battery status', 'system info'

        Special Commands:
        - 'statistics' - Show usage stats
        - 'clear history' - Clear conversation memory
        - 'stop' or 'silence' - Stop speaking

        You can also ask me anything and I'll do my best to help!
        """
        print(help_text)
        self.speaker.say("I've displayed the available commands. "
                         "You can ask me to open apps, check the time, "
                         "control hardware, or just chat with me.")

    def shutdown(self):
        """Gracefully shutdown Jarvis assistant."""
        logger.info("Initiating shutdown sequence...")
        print("\n" + "=" * 60)
        print("[SHUTDOWN] JARVIS SHUTTING DOWN")
        print("=" * 60)

        self.running = False
        self.print_statistics()
        self.speaker.shutdown()

        print("Goodbye!")
        logger.info("Shutdown complete")
        print("=" * 60 + "\n")


def main():
    """Main entry point for Jarvis assistant."""
    try:
        jarvis = JarvisAssistant()
        jarvis.run()

    except KeyboardInterrupt:
        print("\n\nStartup interrupted by user.")
        sys.exit(0)

    except Exception as exc:
        logger.exception("Fatal error during startup")
        print(f"\n[ERROR] Fatal Error: {exc}")
        print("Check jarvis.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
