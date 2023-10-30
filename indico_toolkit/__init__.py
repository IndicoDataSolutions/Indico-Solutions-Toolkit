"""A package to support Indico IPA development"""
__version__ = "6.0.0"

from .errors import *
from .client import create_client
from .retry import retry
