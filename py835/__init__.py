# __init__.py

from .py835 import EDI835Parser  # Assuming py835.py contains the parse function
from .codes import *
from .py835_alpha import Parser

__all__ = [
    'EDI835Parser',
    'Parser',
    'codes'
    ]  
