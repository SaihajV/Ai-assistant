"""
Brain Module - AI Communication and Intelligence
================================================
Handles all communication with Ollama LLM for natural language understanding
and intelligent response generation. Manages conversation history, context,
and response optimization.

Key Features:
- Conversation history management
- Context-aware responses
- Error handling and retry logic
- Response streaming support
- Token management
"""

from typing import List, Dict, Any, Optional
import logging
import ollama
import config

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# BRAIN CLASS - AI COMMUNICATION CORE
# ============================================================================
class Brain:
    """
    AI Brain for Jarvis - Manages LLM communication and conversation state.

    This class handles:
    - Sending messages to Ollama
    - Managing conversation history
    - Maintaining context across interactions
    - Optimizing prompts for better responses
    - Error recovery and retry logic
    """

    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    def __init__(self, system_prompt: Optional[str] = None) -> None:
        """
        Initialize the AI brain with system prompt and conversation history.

        Args:
            system_prompt: Custom system prompt for AI behavior.
                          If None, uses default Jarvis personality.
        """
        # Set system prompt (personality and behavior instructions)
        self.system_prompt = system_prompt or self._get_default_system_prompt()

        # Conversation history storage
        self.history: List[Dict[str, str]] = []

        # Context tracking for better responses
        self.last_topic: Optional[str] = None
        self.interaction_count: int = 0

        logger.info("Brain initialized with model: %s", config.MODEL_NAME)

    # ========================================================================
    # SYSTEM PROMPT CONFIGURATION
    # ========================================================================
    @staticmethod
    def _get_default_system_prompt() -> str:
        """
        Generate the default system prompt for Jarvis personality.

        Returns:
            Comprehensive system prompt defining AI behavior
        """
        return """You are Jarvis, an advanced AI assistant integrated with a voice interface.

Your Core Capabilities:
- Natural conversation in concise, clear responses
- Hardware control through connected devices
- Application launching and system control
- Time and date information
- General knowledge and assistance

Response Guidelines:
- Keep responses brief and conversational (1-3 sentences for simple queries)
- Be helpful, friendly, and professional
- Confirm actions before executing commands
- If unsure, ask for clarification
- Use natural speech patterns suitable for voice output
- Avoid overly technical jargon unless specifically requested

When asked to control hardware:
- Confirm the specific action clearly
- Report success or failure concisely

When asked to open applications:
- Confirm which application is being launched
- Keep confirmation brief

Your personality:
- Professional yet approachable
- Efficient and action-oriented
- Slightly witty when appropriate
- Always respectful and helpful
"""

    # ========================================================================
    # HISTORY MANAGEMENT
    # ========================================================================
    def _trim_history(self) -> None:
        """
        Maintain conversation history within configured limits.

        Keeps only the most recent messages to prevent context overflow
        and maintain response speed. Removes oldest messages first.
        """
        max_length = config.MAX_HISTORY_LENGTH
        excess = len(self.history) - max_length

        if excess > 0:
            removed = self.history[:excess]
            self.history = self.history[excess:]
            logger.debug("Trimmed %d messages from history", excess)

    def clear_history(self) -> None:
        """
        Clear all conversation history.

        Useful for starting fresh conversations or when context
        becomes confusing or irrelevant.
        """
        message_count = len(self.history)
        self.history.clear()
        self.last_topic = None
        self.interaction_count = 0
        logger.info("Cleared conversation history (%d messages)", message_count)

    def get_history_summary(self) -> str:
        """
        Get a summary of the current conversation state.

        Returns:
            Human-readable summary of conversation history
        """
        if not self.history:
            return "No conversation history"

        user_msgs = sum(1 for msg in self.history if msg["role"] == "user")
        assistant_msgs = sum(1 for msg in self.history if msg["role"] == "assistant")

        return (f"History: {len(self.history)} messages "
                f"({user_msgs} user, {assistant_msgs} assistant)")

    # ========================================================================
    # CORE CHAT FUNCTIONALITY
    # ========================================================================
    def chat(self, user_message: str, temperature: Optional[float] = None) -> str:
        """
        Send a message to the AI model and get a response.

        This is the main interface for conversing with the AI. It:
        1. Adds the user message to history
        2. Constructs the full conversation context
        3. Sends to Ollama for processing
        4. Stores and returns the response

        Args:
            user_message: The user's input text
            temperature: Override default temperature for this request
                        (higher = more creative, lower = more focused)

        Returns:
            The AI's response text, or an error message if something fails
        """
        try:
            # ================================================================
            # STEP 1: Add user message to history
            # ================================================================
            self.history.append({"role": "user", "content": user_message})
            self.interaction_count += 1
            logger.debug("User message added to history (interaction #%d)",
                         self.interaction_count)

            # Trim history if needed
            self._trim_history()

            # ================================================================
            # STEP 2: Build message context
            # ================================================================
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": self.system_prompt}
            ]

            # Add conversation history for context
            if config.ENABLE_CONTEXT:
                messages.extend(self.history)
            else:
                # Without context, only use the current message
                messages.append(self.history[-1])

            logger.debug("Sending %d messages to model", len(messages))

            # ================================================================
            # STEP 3: Call Ollama API
            # ================================================================
            response: Dict[str, Any] = ollama.chat(
                model=config.MODEL_NAME,
                messages=messages,
                options={
                    "temperature": temperature or config.MODEL_TEMPERATURE,
                    "num_predict": config.MODEL_MAX_TOKENS,
                }
            )

            # ================================================================
            # STEP 4: Extract and store response
            # ================================================================
            assistant_reply = response.get("message", {}).get("content", "").strip()

            if not assistant_reply:
                logger.warning("Received empty response from model")
                return "I apologize, but I didn't generate a response. Could you rephrase that?"

            # Add assistant response to history
            self.history.append({"role": "assistant", "content": assistant_reply})
            self._trim_history()

            logger.info("Response generated successfully (%d chars)",
                        len(assistant_reply))

            return assistant_reply

        except Exception as ollama_exc:
            # Check if it's an Ollama ResponseError (if it exists)
            if hasattr(ollama, "ResponseError") and isinstance(ollama_exc, ollama.ResponseError):
                # ================================================================
                # HANDLE OLLAMA-SPECIFIC ERRORS
                # ================================================================
                logger.error("Ollama API error: %s", ollama_exc)
                return (f"I encountered an issue with the AI model: {ollama_exc}. "
                        "Please make sure Ollama is running and the model is available.")
            elif isinstance(ollama_exc, ConnectionError):
                # ================================================================
                # HANDLE CONNECTION ERRORS
                # ================================================================
                logger.error("Connection error: %s", ollama_exc)
                return ("I can't connect to the AI model right now. "
                        "Please make sure Ollama is installed and running on your system. "
                        "You can download it from https://ollama.com/download")
            else:
                # Re-raise to be caught by outer exception handler
                raise

        except Exception as exc:
            # ================================================================
            # HANDLE UNEXPECTED ERRORS
            # ================================================================
            logger.exception("Unexpected error in chat")
            return f"I encountered an unexpected error: {exc}"

    # ========================================================================
    # ADVANCED FEATURES
    # ========================================================================
    def chat_with_context(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Enhanced chat that includes additional context information.

        Useful for providing the AI with current system state, recent actions,
        or other relevant information that helps generate better responses.

        Args:
            user_message: The user's input text
            context: Additional context (e.g., hardware state, recent actions)

        Returns:
            The AI's contextually-aware response
        """
        # Build enhanced message with context
        context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
        enhanced_message = f"{user_message}\n\nCurrent Context:\n{context_str}"

        logger.debug("Chat with context: %s", context.keys())
        return self.chat(enhanced_message)

    def get_intent(self, user_message: str) -> str:
        """
        Analyze user message to determine intent/category.

        This can be used for better routing to skills or understanding
        what the user wants to accomplish.

        Args:
            user_message: The user's input text

        Returns:
            Detected intent category (e.g., "question", "command", "conversation")
        """
        intent_prompt = (
            f"Analyze this message and respond with only ONE word: "
            f"'QUESTION' if asking for information, "
            f"'COMMAND' if requesting an action, "
            f"or 'CONVERSATION' if just chatting.\n\n"
            f"Message: {user_message}"
        )

        try:
            response = self.chat(intent_prompt, temperature=0.1)
            intent = response.strip().upper()
            logger.debug("Detected intent: %s", intent)
            return intent if intent in ["QUESTION", "COMMAND", "CONVERSATION"] else "UNKNOWN"
        except Exception as exc:
            logger.error("Intent detection failed: %s", exc)
            return "UNKNOWN"

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    def set_system_prompt(self, new_prompt: str) -> None:
        """
        Update the system prompt (AI personality/behavior).

        Args:
            new_prompt: New system prompt text
        """
        self.system_prompt = new_prompt
        logger.info("System prompt updated")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the brain's operation.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "model": config.MODEL_NAME,
            "history_length": len(self.history),
            "max_history": config.MAX_HISTORY_LENGTH,
            "interactions": self.interaction_count,
            "context_enabled": config.ENABLE_CONTEXT,
            "last_topic": self.last_topic
        }