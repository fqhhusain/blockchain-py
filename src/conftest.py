"""
conftest.py  (lives in src/)
-----------------------------
Makes all modules under src/ importable when running pytest from src/ or
from the project root with  pytest src/tests/.
"""
import os
import sys

# Ensure the src/ directory is on the path so test files can do:
#   from core.wallet import generate_keys
#   from app import create_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))