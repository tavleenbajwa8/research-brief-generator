#!/usr/bin/env python3
"""
CLI Entry Point for Research Brief Generator

This script provides command-line access to the research brief generator.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.cli import cli

if __name__ == '__main__':
    cli() 