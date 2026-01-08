"""
Configuration Module for Jarvis Voice Assistant
===============================================
Manages all configuration settings, environment variables, and constants.
Loads secrets from .env file with intelligent fallback to defaults.

Configuration Categories:
- Wake words and activation
- AI model settings
- Hardware control endpoints
- Application paths
- Audio/Voice settings
- System paths and directories
"""

import os
import json
import logging
from typing import Dict, List
from pathlib import Path
## from dotenv import load_dotenv

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
# Load environment variables from .env file (should be in project root)
##load_dotenv()

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Configure logging level from environment (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# WAKE WORDS & ACTIVATION
# ============================================================================
# Wake words that trigger command processing
# Can be extended with additional phrases as needed
WAKE_WORDS: List[str] = ["jarvis", "hey jarvis"]

# Optional: Additional stop words for emergency stop
STOP_WORDS: List[str] = ["stop", "silence", "quiet", "shut up"]

# ============================================================================
# AI MODEL CONFIGURATION
# ============================================================================
# Ollama model name - supports any Ollama-compatible model
# Popular options: llama3, mistral, codellama, neural-chat
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
MODEL_NAME: str = OLLAMA_MODEL  # Backward compatibility alias

# Ollama API endpoint (default: local installation)
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model parameters for response generation
MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", "500"))

# ============================================================================
# HARDWARE CONTROL SETTINGS
# ============================================================================
# ESP32 IP address for hardware control commands
# Update this in .env file with your ESP32's actual IP
ESP32_IP: str = os.getenv("ESP32_IP", "192.168.1.50")

# Hardware communication timeout (seconds)
HARDWARE_TIMEOUT: int = int(os.getenv("HARDWARE_TIMEOUT", "3"))

# ============================================================================
# APPLICATION PATHS
# ============================================================================
# JSON string mapping application names to their executable paths
# Format: {"app_name": "/path/to/app.exe", "another_app": "/path/to/another"}
APP_PATHS_JSON: str = os.getenv("APP_PATHS_JSON", "{}")


# Helper function for debug logging
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str = "A"):
    """Write debug log entry safely."""
    try:
        Path(".cursor").mkdir(exist_ok=True)
        with open(".cursor/debug.log", "a") as f:
            import json as json_module
            import time
            f.write(json_module.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": time.time() * 1000
            }) + "\n")
    except:
        pass


# Parse application paths with error handling
def _load_app_paths() -> Dict[str, str]:
    """
    Parse and validate application paths from JSON configuration.

    Returns:
        Dictionary mapping application names to their file paths
    """
    # #region agent log
    _debug_log("config.py:_load_app_paths:87", "Function entry", {"app_paths_json": APP_PATHS_JSON[:100] if APP_PATHS_JSON else "empty"})
    # #endregion
    try:
        if not APP_PATHS_JSON:
            return {}
        paths = json.loads(APP_PATHS_JSON)
        # #region agent log
        _debug_log("config.py:_load_app_paths:90", "JSON parsed successfully", {"path_count": len(paths)})
        # #endregion
        # Validate that all paths exist and log warnings for missing ones
        validated_paths = {}
        for app_name, path in paths.items():
            if os.path.exists(path):
                validated_paths[app_name] = path
            else:
                # #region agent log
                _debug_log("config.py:_load_app_paths:97", "Before logging.warning call", {"app_name": app_name, "path": path})
                # #endregion
                try:
                    logging.warning(f"Configured path for '{app_name}' not found: {path}")
                except Exception as log_exc:
                    # #region agent log
                    _debug_log("config.py:_load_app_paths:97", "logging.warning failed", {"error": str(log_exc)})
                    # #endregion
                    pass
        return validated_paths
    except json.JSONDecodeError as e:
        # #region agent log
        _debug_log("config.py:_load_app_paths:100", "Before logging.error call", {"error": str(e)})
        # #endregion
        try:
            logging.error(f"Invalid JSON in APP_PATHS_JSON: {e}")
        except Exception as log_exc:
            # #region agent log
            _debug_log("config.py:_load_app_paths:100", "logging.error failed", {"error": str(log_exc)})
            # #endregion
            pass
        return {}


APP_PATHS: Dict[str, str] = _load_app_paths()

# ============================================================================
# AUDIO & VOICE SETTINGS
# ============================================================================
# Text-to-speech voice parameters
DEFAULT_VOICE_RATE: int = int(os.getenv("VOICE_RATE", "175"))  # Words per minute
DEFAULT_VOICE_VOLUME: float = float(os.getenv("VOICE_VOLUME", "0.9"))  # 0.0 to 1.0

# Speech recognition parameters
SPEECH_ENERGY_THRESHOLD: int = int(os.getenv("ENERGY_THRESHOLD", "300"))
SPEECH_PAUSE_THRESHOLD: float = float(os.getenv("PAUSE_THRESHOLD", "0.6"))
SPEECH_PHRASE_TIME_LIMIT: int = int(os.getenv("PHRASE_TIME_LIMIT", "8"))

# ============================================================================
# CONVERSATION SETTINGS
# ============================================================================
# Maximum number of messages to keep in conversation history
MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "10"))

# Enable context-aware responses (remembers previous conversation)
ENABLE_CONTEXT: bool = os.getenv("ENABLE_CONTEXT", "true").lower() == "true"

# ============================================================================
# SYSTEM PATHS & DIRECTORIES
# ============================================================================
# Base directory for data storage (logs, recordings, etc.)
DATA_DIR: str = os.getenv("DATA_DIR", "data")
try:
    Path(DATA_DIR).mkdir(exist_ok=True)  # Ensure directory exists
except Exception:
    # If directory creation fails, continue with default
    pass

# Log file location
LOG_FILE: str = os.path.join(DATA_DIR, "jarvis.log")

# Ensure .cursor directory exists for debug logs
try:
    Path(".cursor").mkdir(exist_ok=True)
except Exception:
    pass

# ============================================================================
# FEATURE FLAGS
# ============================================================================
# Enable/disable specific features
ENABLE_HARDWARE_CONTROL: bool = os.getenv("ENABLE_HARDWARE", "true").lower() == "true"
ENABLE_APP_LAUNCH: bool = os.getenv("ENABLE_APP_LAUNCH", "true").lower() == "true"
ENABLE_WEB_SEARCH: bool = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================
def validate_config() -> bool:
    """
    Validate critical configuration settings on startup.

    Returns:
        True if configuration is valid, False otherwise
    """
    issues = []

    if not WAKE_WORDS:
        issues.append("No wake words configured")

    if not OLLAMA_MODEL:
        issues.append("No AI model specified")

    if ENABLE_HARDWARE_CONTROL and not ESP32_IP:
        issues.append("Hardware control enabled but no ESP32_IP set")

    if issues:
        for issue in issues:
            try:
                logging.error(f"Config issue: {issue}")
            except Exception:
                # Logging not configured yet, use print as fallback
                print(f"Config issue: {issue}")
        return False

    return True


# ============================================================================
# CONFIGURATION EXPORT
# ============================================================================
def get_config_summary() -> Dict:
    """
    Get a summary of current configuration for debugging.

    Returns:
        Dictionary with non-sensitive configuration values
    """
    return {
        "model": OLLAMA_MODEL,
        "wake_words": WAKE_WORDS,
        "hardware_enabled": ENABLE_HARDWARE_CONTROL,
        "app_launch_enabled": ENABLE_APP_LAUNCH,
        "max_history": MAX_HISTORY_LENGTH,
        "voice_rate": DEFAULT_VOICE_RATE,
        "log_level": LOG_LEVEL
    }