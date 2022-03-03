"""A package to support Indico IPA development"""
__version__ = "1.2.2"

from .errors import *
from .client import create_client
from .retry import retry
