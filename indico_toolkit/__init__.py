"""A package to support Indico IPA development"""
__version__ = "2.0.0"

from .errors import *
from .client import create_client
from .retry import retry

from indico_toolkit.indico_wrapper import (
    IndicoWrapper,
    retry,
    Workflow,
    Datasets,
    Reviewer,
    DocExtraction,
    Download
)

from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.snapshots import Snapshot
from indico_toolkit.metrics import ExtractionMetrics, CompareModels, Plotting
from indico_toolkit.highlighter import Highlighter
