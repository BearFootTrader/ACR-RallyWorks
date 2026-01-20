#!/usr/bin/env python3
"""
Rally Car Setup Calculator - Launcher
Run this file to start the application
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from gui import main

if __name__ == "__main__":
    main()
