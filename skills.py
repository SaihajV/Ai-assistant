"""
Skills Module - Action Execution and Commands
==============================================
Maps keywords to executable actions and commands. This is the "action layer"
that handles specific tasks like opening apps, controlling hardware, etc.

Key Features:
- Application launching
- Hardware control
- Time and date functions
- Web search capabilities (optional)
- Extensible skill system
"""

from datetime import datetime
import os
import platform
import subprocess
import logging
from typing import Callable, Dict, Any, Optional, List
import requests
import config

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)


# ============================================================================
# SKILL CATEGORIES
# ============================================================================

# ===========================================================================
# CATEGORY: APPLICATION CONTROL
# ===========================================================================
def open_app(app_name: str) -> str:
    """
    Open an application using the most appropriate method for the OS.

    Priority order:
    1. Check config.APP_PATHS for explicitly configured path
    2. Try generic OS launch command
    3. Fall back to error message

    Args:
        app_name: Name of the application to open (case-insensitive)

    Returns:
        Status message indicating success or failure
    """
    logger.info("Attempting to open application: %s", app_name)

    # ========================================================================
    # STEP 1: Normalize app name for lookup
    # ========================================================================
    system = platform.system().lower()
    lookup_key = app_name.lower().strip()

    # ========================================================================
    # STEP 2: Try configured path first (most reliable)
    # ========================================================================
    app_path = config.APP_PATHS.get(lookup_key)

    if app_path:
        # Check if configured path actually exists
        if os.path.exists(app_path):
            try:
                subprocess.Popen([app_path])
                logger.info("Opened %s from configured path", lookup_key)
                return f"Opening {app_name}."
            except Exception as exc:
                logger.error("Failed to open %s: %s", lookup_key, exc)
                return f"Failed to open {app_name}: {exc}"
        else:
            logger.warning("Configured path for %s not found: %s", lookup_key, app_path)
            return f"The configured path for {app_name} was not found. Please update your configuration."

    # ========================================================================
    # STEP 3: Try OS-specific launch command
    # ========================================================================
    try:
        if system == "windows":
            # Windows: use 'start' command
            subprocess.Popen(["start", "", app_name], shell=True)
            logger.info("Opened %s using Windows start command", app_name)

        elif system == "darwin":
            # macOS: use 'open' command
            subprocess.Popen(["open", "-a", app_name])
            logger.info("Opened %s using macOS open command", app_name)

        else:
            # Linux and others: try direct execution
            subprocess.Popen([app_name])
            logger.info("Opened %s using direct execution", app_name)

        return f"Opening {app_name}."

    except FileNotFoundError:
        logger.warning("Application not found: %s", app_name)
        return (f"Could not find {app_name}. "
                f"Try adding its full path to your configuration.")

    except Exception as exc:
        logger.error("Unexpected error opening %s: %s", app_name, exc)
        return f"Failed to open {app_name}: {exc}"


def close_app(app_name: str) -> str:
    """
    Attempt to close a running application (platform-dependent).

    Args:
        app_name: Name of the application to close

    Returns:
        Status message
    """
    system = platform.system().lower()

    try:
        if system == "windows":
            subprocess.run(["taskkill", "/IM", f"{app_name}.exe", "/F"],
                           capture_output=True, check=True)
        elif system == "darwin":
            subprocess.run(["pkill", "-f", app_name], check=True)
        else:
            subprocess.run(["pkill", app_name], check=True)

        logger.info("Closed application: %s", app_name)
        return f"Closed {app_name}."

    except subprocess.CalledProcessError:
        logger.warning("Could not close %s - may not be running", app_name)
        return f"{app_name} is not running or could not be closed."
    except Exception as exc:
        logger.error("Error closing %s: %s", app_name, exc)
        return f"Failed to close {app_name}: {exc}"


# ===========================================================================
# CATEGORY: TIME AND DATE
# ===========================================================================
def get_time() -> str:
    """
    Get the current time in 12-hour format.

    Returns:
        Formatted time string (e.g., "02:30 PM")
    """
    current_time = datetime.now().strftime("%I:%M %p")
    logger.debug("Time requested: %s", current_time)
    return f"The time is {current_time}"


def get_date() -> str:
    """
    Get the current date in readable format.

    Returns:
        Formatted date string (e.g., "Monday, January 15, 2024")
    """
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    logger.debug("Date requested: %s", current_date)
    return f"Today is {current_date}"


def get_datetime() -> str:
    """
    Get both date and time.

    Returns:
        Combined date and time string
    """
    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    return f"It's {time_str} on {date_str}"


# ===========================================================================
# CATEGORY: HARDWARE CONTROL
# ===========================================================================
def control_hardware(action: str = "status") -> str:
    """
    Send commands to ESP32 or other connected hardware.

    This function communicates with an ESP32 device over HTTP to control
    connected hardware (lights, sensors, actuators, etc.)

    Common actions:
    - status: Get current hardware state
    - on: Turn device on
    - off: Turn device off
    - toggle: Toggle device state

    Args:
        action: Command to send to the hardware (default: "status")

    Returns:
        Response from hardware or error message
    """
    if not config.ENABLE_HARDWARE_CONTROL:
        return "Hardware control is currently disabled."

    # ========================================================================
    # STEP 1: Build request URL
    # ========================================================================
    url = f"http://{config.ESP32_IP}/{action}"
    logger.info("Sending hardware command: %s to %s", action, config.ESP32_IP)

    # ========================================================================
    # STEP 2: Send HTTP request to hardware
    # ========================================================================
    try:
        response = requests.get(
            url,
            timeout=config.HARDWARE_TIMEOUT
        )
        response.raise_for_status()

        # ====================================================================
        # STEP 3: Process response
        # ====================================================================
        body = response.text.strip()

        if body:
            logger.info("Hardware response: %s", body)
            return body
        else:
            logger.info("Hardware responded with status %d", response.status_code)
            return f"Hardware command executed successfully (status {response.status_code})."

    except requests.Timeout:
        logger.error("Hardware request timed out")
        return f"Hardware did not respond within {config.HARDWARE_TIMEOUT} seconds."

    except requests.ConnectionError:
        logger.error("Could not connect to hardware at %s", config.ESP32_IP)
        return (f"Could not connect to hardware at {config.ESP32_IP}. "
                f"Please check the IP address and network connection.")

    except requests.RequestException as exc:
        logger.error("Hardware control failed: %s", exc)
        return f"Hardware control failed: {exc}"


# ===========================================================================
# CATEGORY: SYSTEM INFORMATION
# ===========================================================================
def get_system_info() -> str:
    """
    Get basic system information.

    Returns:
        System info string with OS, platform, and Python version
    """
    system = platform.system()
    release = platform.release()
    machine = platform.machine()

    info = (f"Running on {system} {release}, "
            f"{machine} architecture")

    logger.debug("System info: %s", info)
    return info


def get_battery_status() -> str:
    """
    Get battery status (if available).

    Returns:
        Battery level and charging status, or unavailable message
    """
    try:
        import psutil
        battery = psutil.sensors_battery()

        if battery is None:
            return "Battery information is not available on this system."

        percent = battery.percent
        plugged = "charging" if battery.power_plugged else "not charging"

        logger.debug("Battery: %d%% (%s)", percent, plugged)
        return f"Battery is at {percent}% and {plugged}."

    except ImportError:
        return "Battery monitoring requires psutil package."
    except Exception as exc:
        logger.error("Error getting battery status: %s", exc)
        return f"Could not get battery status: {exc}"


# ===========================================================================
# CATEGORY: WEB AND NETWORK
# ===========================================================================
def search_web(query: str) -> str:
    """
    Open web browser with search query (requires ENABLE_WEB_SEARCH flag).

    Args:
        query: Search terms

    Returns:
        Status message
    """
    if not config.ENABLE_WEB_SEARCH:
        return "Web search is currently disabled."

    import webbrowser

    try:
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)
        logger.info("Opened web search for: %s", query)
        return f"Searching the web for {query}."
    except Exception as exc:
        logger.error("Web search failed: %s", exc)
        return f"Failed to open web search: {exc}"


# ===========================================================================
# CATEGORY: VOLUME CONTROL
# ===========================================================================
def adjust_volume(direction: str = "up") -> str:
    """
    Adjust system volume (platform-dependent).

    Args:
        direction: "up", "down", or "mute"

    Returns:
        Status message
    """
    system = platform.system().lower()

    try:
        if system == "windows":
            # Windows volume control via nircmd (if installed)
            # Or use ctypes for volume control
            # #region agent log
            try:
                with open(r"d:\# CODE\1 CODE\.vscode\Arduino Project\ai\.cursor\debug.log", "a") as f:
                    import json as json_module
                    f.write(json_module.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "skills.py:adjust_volume:341", "message": "Before optional imports", "data": {"system": system}, "timestamp": __import__("time").time() * 1000}) + "\n")
            except: pass
            # #endregion
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                # #region agent log
                try:
                    with open(r"d:\# CODE\1 CODE\.vscode\Arduino Project\ai\.cursor\debug.log", "a") as f:
                        import json as json_module
                        f.write(json_module.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "skills.py:adjust_volume:344", "message": "Optional imports successful", "data": {}, "timestamp": __import__("time").time() * 1000}) + "\n")
                except: pass
                # #endregion
                
                # Use the imported modules
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))

                if direction == "up":
                    current = volume.GetMasterVolumeLevelScalar()
                    volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
                    return "Volume increased."
                elif direction == "down":
                    current = volume.GetMasterVolumeLevelScalar()
                    volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
                    return "Volume decreased."
                elif direction == "mute":
                    volume.SetMute(1, None)
                    return "Volume muted."
            except ImportError as import_err:
                # #region agent log
                try:
                    with open(r"d:\# CODE\1 CODE\.vscode\Arduino Project\ai\.cursor\debug.log", "a") as f:
                        import json as json_module
                        f.write(json_module.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "skills.py:adjust_volume:362", "message": "Optional imports failed", "data": {"error": str(import_err)}, "timestamp": __import__("time").time() * 1000}) + "\n")
                except: pass
                # #endregion
                return "Volume control requires additional packages for your system."

        elif system == "darwin":
            # macOS volume control
            if direction == "up":
                subprocess.run(["osascript", "-e",
                                "set volume output volume (output volume of (get volume settings) + 10)"])
            elif direction == "down":
                subprocess.run(["osascript", "-e",
                                "set volume output volume (output volume of (get volume settings) - 10)"])
            elif direction == "mute":
                subprocess.run(["osascript", "-e", "set volume output muted true"])
            return f"Volume {direction}."

        else:
            # Linux volume control (requires amixer)
            if direction == "up":
                subprocess.run(["amixer", "set", "Master", "5%+"], check=True)
            elif direction == "down":
                subprocess.run(["amixer", "set", "Master", "5%-"], check=True)
            elif direction == "mute":
                subprocess.run(["amixer", "set", "Master", "toggle"], check=True)
            return f"Volume {direction}."

    except ImportError:
        return "Volume control requires additional packages for your system."
    except Exception as exc:
        logger.error("Volume control failed: %s", exc)
        return f"Could not adjust volume: {exc}"


# ============================================================================
# SKILLS REGISTRY - KEYWORD TO FUNCTION MAPPING
# ============================================================================
"""
The SKILLS dictionary maps keywords (trigger words/phrases) to functions.

When a keyword is detected in user input, the corresponding function is called.
Longer keywords are matched first to handle phrases like "what time" vs "time".

Add new skills by:
1. Defining a function above
2. Adding an entry here: "keyword": function_name
"""

SKILLS: Dict[str, Callable[..., Any]] = {
    # Application Control
    "open": open_app,
    "launch": open_app,
    "start": open_app,
    "run": open_app,
    "close": close_app,
    "quit": close_app,

    # Time and Date
    "what time": get_time,
    "time": get_time,
    "what date": get_date,
    "date": get_date,
    "what day": get_date,
    "date and time": get_datetime,

    # Hardware Control
    "hardware": control_hardware,
    "lights": lambda: control_hardware("lights"),
    "turn on": lambda: control_hardware("on"),
    "turn off": lambda: control_hardware("off"),

    # System Information
    "system info": get_system_info,
    "battery": get_battery_status,

    # Web and Search
    "search": search_web,
    "google": search_web,

    # Volume Control
    "volume up": lambda: adjust_volume("up"),
    "volume down": lambda: adjust_volume("down"),
    "mute": lambda: adjust_volume("mute"),
}


# ============================================================================
# SKILL MANAGEMENT FUNCTIONS
# ============================================================================

def register_skill(keyword: str, function: Callable) -> None:
    """
    Dynamically register a new skill.

    Args:
        keyword: Trigger word/phrase for the skill
        function: Function to call when keyword is detected
    """
    SKILLS[keyword.lower()] = function
    logger.info("Registered new skill: %s", keyword)


def unregister_skill(keyword: str) -> bool:
    """
    Remove a skill from the registry.

    Args:
        keyword: Skill keyword to remove

    Returns:
        True if skill was removed, False if not found
    """
    keyword_lower = keyword.lower()
    if keyword_lower in SKILLS:
        del SKILLS[keyword_lower]
        logger.info("Unregistered skill: %s", keyword)
        return True
    return False


def list_skills() -> List[str]:
    """
    Get list of all registered skill keywords.

    Returns:
        Sorted list of skill keywords
    """
    return sorted(SKILLS.keys())


def get_skill_info() -> Dict[str, str]:
    """
    Get information about all registered skills.

    Returns:
        Dictionary mapping keywords to function names
    """
    return {
        keyword: func.__name__
        for keyword, func in SKILLS.items()
    }


def print_skills() -> None:
    """Print all available skills to console."""
    print("\n=== Available Skills ===")
    for keyword in sorted(SKILLS.keys()):
        func = SKILLS[keyword]
        print(f"  {keyword:20} -> {func.__name__}")
    print("========================\n")