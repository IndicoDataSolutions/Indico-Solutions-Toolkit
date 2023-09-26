"""A package to support Indico IPA development"""
__version__ = "2.0.2"

from .errors import *
from .client import create_client
from .retry import retry
