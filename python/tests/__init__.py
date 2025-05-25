# This file makes the tests directory a Python package
import sys
import os

# Add the parent directory to the path to import versioned_ds
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from versioned_ds import SimpleKafka
from time_ds import CalendarQueue

__all__ = ['SimpleKafka', 'CalendarQueue'] 
