"""
A feature-complete auto review polling script that incorporates asyncio,
automatic retry, result file dataclasses, and etl output dataclasses.

Max workers, spawn rate, etl output loading, and retry behavior are all configurable.
See the `AutoReviewPoller` class definition.
"""

import asyncio
import sys

from indico import IndicoConfig

from indico_toolkit.polling import AutoReviewPoller, AutoReviewed
from indico_toolkit.etloutput import EtlOutput
from indico_toolkit.results import Result, Document


async def auto_review(
    result: Result, etl_outputs: dict[Document, EtlOutput]
) -> AutoReviewed:
    """
    Apply auto review rules to predictions and determine straight through processing.
    Any IO performed (network requests, file reads/writes, etc) must be awaited to
    avoid blocking the asyncio loop that schedules this coroutine.
    """
    predictions = result.pre_review

    # Apply auto review rules.

    return AutoReviewed(
        changes=predictions.to_changes(result),
        stp=True,  # Defaults to `False` and may be omitted.
    )


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        format=(
            r"[%(asctime)s] "
            r"%(name)s:%(funcName)s():%(lineno)s: "
            r"%(levelname)s %(message)s"
        ),
        level=logging.INFO,
        force=True,
    )
    workflow_id = int(sys.argv[1])
    asyncio.run(
        AutoReviewPoller(
            IndicoConfig(
                host="try.indico.io",
                api_token_path="indico_api_token.txt",
            ),
            workflow_id,
            auto_review,
        ).poll_forever()
    )
