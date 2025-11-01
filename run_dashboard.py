#!/usr/bin/env python3
"""
Startup script for Deep Research Dashboard
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.app import main

if __name__ == '__main__':
    main()
