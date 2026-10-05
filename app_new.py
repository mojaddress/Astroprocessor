"""
Astro Processor - Main Entry Point (Streamlit)
This is a thin wrapper that delegates to the new architecture in ui_streamlit/app_streamlit.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the new Streamlit app
from ui_streamlit.app_streamlit import main as run_app

if __name__ == "__main__":
    run_app()