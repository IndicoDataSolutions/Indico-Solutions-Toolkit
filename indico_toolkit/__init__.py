"""A package to support Indico IPA development"""
__version__ = "1.0.5"

from .errors import *
from .client import create_client
from .retry import retry
