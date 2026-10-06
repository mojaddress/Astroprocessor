"""
Unified Path Resolution - handles paths for both frozen (PyInstaller) and development environments.
"""
import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Check if running in a PyInstaller frozen executable."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_app_dir() -> Path:
    """
    Get the application directory.
    - Frozen: directory containing the .exe
    - Dev: project root directory
    """
    if is_frozen():
        return Path(sys.executable).parent
    else:
        # In development, go up from this file to project root
        return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    Get the user data directory for persistent storage.
    Uses %APPDATA%/AstroProcessor on Windows.
    """
    if is_frozen():
        # In frozen mode, use APPDATA
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / "AstroProcessor"
    
    # Fallback for dev or if APPDATA not set
    return get_app_dir() / "data"


def get_ephe_dir() -> Path:
    """
    Get the ephemeris directory.
    - Frozen: _MEIPASS/ephe (bundled) or app_dir/ephe (external)
    - Dev: project_root/ephe
    """
    if is_frozen():
        # Check if ephe is bundled in _MEIPASS
        meipass_ephe = Path(sys._MEIPASS) / "ephe"
        if meipass_ephe.exists():
            return meipass_ephe
        
        # Fallback to app_dir/ephe
        return get_app_dir() / "ephe"
    else:
        return get_app_dir() / "ephe"


def get_cities_file() -> Path:
    """Get the cities.json file path."""
    if is_frozen():
        meipass_cities = Path(sys._MEIPASS) / "data" / "cities.json"
        if meipass_cities.exists():
            return meipass_cities
        return get_app_dir() / "data" / "cities.json"
    else:
        return get_app_dir() / "data" / "cities.json"


def get_config_dir() -> Path:
    """Get the configuration directory."""
    if is_frozen():
        return get_data_dir() / "config"
    else:
        return get_app_dir() / "config"


def get_profiles_dir() -> Path:
    """Get the profiles directory."""
    if is_frozen():
        return get_data_dir() / "profiles"
    else:
        return get_app_dir() / "profiles"


def get_display_profiles_dir() -> Path:
    """Get the display profiles directory."""
    if is_frozen():
        # Check bundled first
        meipass_dp = Path(sys._MEIPASS) / "config" / "display_profiles"
        if meipass_dp.exists():
            return meipass_dp
        return get_data_dir() / "config" / "display_profiles"
    else:
        return get_app_dir() / "config" / "display_profiles"


def get_log_dir() -> Path:
    """Get the log directory."""
    if is_frozen():
        return get_data_dir() / "logs"
    else:
        return get_app_dir() / "logs"


def ensure_dirs():
    """Create all necessary directories."""
    dirs = [
        get_data_dir(),
        get_config_dir(),
        get_profiles_dir(),
        get_display_profiles_dir(),
        get_log_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# Legacy compatibility - for existing code that expects these paths
def get_default_ephe_path() -> str:
    """Get default ephe path as string."""
    return str(get_ephe_dir())


def get_default_cities_file() -> str:
    """Get default cities file path as string."""
    return str(get_cities_file())


def get_default_profiles_dir() -> str:
    """Get default profiles dir as string."""
    return str(get_profiles_dir())


def get_default_display_profiles_dir() -> str:
    """Get default display profiles dir as string."""
    return str(get_display_profiles_dir())