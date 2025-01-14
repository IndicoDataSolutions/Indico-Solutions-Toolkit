import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from indico import AsyncIndicoClient, IndicoConfig  # type: ignore[import-untyped]
from indico.errors import IndicoError  # type: ignore[import-untyped]
from indico.queries import (  # type: ignore[import-untyped]
    GetSubmission,
    JobStatus,
    RetrieveStorageObject,
    SubmitReview,
)

from .. import etloutput, results
from ..etloutput import EtlOutput
from ..results import Document, Result
from ..retry import retry
from .queries import SubmissionIdsPendingAutoReview

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import Any, TypeAlias

    SubmissionId: TypeAlias = int
    Worker: TypeAlias = asyncio.Task[None]
    WorkerQueue: TypeAlias = asyncio.Queue[tuple[SubmissionId, Worker]]

logger = logging.getLogger(__name__)


@dataclass
class AutoReviewed:
    changes: "dict[str, Any] | list[dict[str, Any]]"
    stp: bool = False


class AutoReviewPoller:
    """
    Polls for submissions requiring auto review, processes them concurrently,
    and submits the review results.
    """

    def __init__(
        self,
        config: IndicoConfig,
        workflow_id: int,
        auto_review: "Callable[[Result, dict[Document, EtlOutput]], Awaitable[AutoReviewed]]",  # noqa: E501
        *,
        concurrency: int = 8,
        enqueue_delay: float = 1,
        poll_delay: float = 30,
        load_etl_output: bool = True,
        load_text: bool = True,
        load_tokens: bool = True,
        load_tables: bool = False,
        retry_count: int = 4,
        retry_wait: float = 1,
        retry_backoff: float = 4,
        retry_jitter: float = 0.5,
    ):
        self._config = config
        self._workflow_id = workflow_id
        self._concurrency = concurrency
        self._auto_review = auto_review
        self._enqueue_delay = enqueue_delay
        self._poll_delay = poll_delay
        self._load_etl_output = load_etl_output
        self._load_text = load_text
        self._load_tokens = load_tokens
        self._load_tables = load_tables

        self._retry = retry(
            IndicoError,
            retry_count,
            retry_wait,
            retry_backoff,
            retry_jitter,
        )
        self._worker_slots = asyncio.Semaphore(concurrency)
        self._worker_queue: WorkerQueue = asyncio.Queue(1)
        self._processing_submission_ids: set[SubmissionId] = set()

    async def run(self) -> None:
        logger.info(
            "Starting auto review poller for: "
            f"host={self._config.host} "
            f"workflow_id={self._workflow_id}"
            f"concurrency={self._concurrency}"
        )

        async with AsyncIndicoClient(self._config) as client:
            self._client_call = self._retry(client.call)
            await asyncio.gather(
                self._spawn_workers(),
                *(self._reap_workers() for _ in range(self._concurrency)),
            )

    async def _retrieve_storage_object(self, url: str) -> object:
        return await self._client_call(RetrieveStorageObject(url))

    async def _spawn_workers(self) -> None:
        """
        Poll for submissions pending auto review and spawn workers to process them.
        `self._worker_slots` limits the number of workers that can run concurrently.
        Submission IDs in progress are tracked with `self._processing_submission_ids`.
        """
        logger.info(
            f"Polling submissions pending auto review every {self._poll_delay} seconds"
        )

        while True:
            try:
                submission_ids: set[int] = await self._client_call(
                    SubmissionIdsPendingAutoReview(self._workflow_id)
                )
            except Exception:
                logger.exception("Error occurred while polling submissions")
                await asyncio.sleep(self._poll_delay)
                continue

            submission_ids -= self._processing_submission_ids

            if not submission_ids:
                await asyncio.sleep(self._poll_delay)
                continue

            for submission_id in submission_ids:
                await self._worker_slots.acquire()
                logger.info(f"Spawning worker for {submission_id=}")
                self._processing_submission_ids.add(submission_id)
                worker = asyncio.create_task(self._worker(submission_id))
                await self._worker_queue.put((submission_id, worker))
                await asyncio.sleep(self._enqueue_delay)

    async def _worker(self, submission_id: SubmissionId) -> None:
        """
        Process a single submission by retrieving submission metadata, the result file,
        etl output, calling `self._auto_review`, and submitting changes.
        """
        logger.info(f"Retrieving metadata for {submission_id=}")
        submission = await self._client_call(GetSubmission(submission_id))

        logger.info(f"Retrieving results for {submission_id=}")
        result = await results.load_async(
            submission.result_file,
            reader=self._retrieve_storage_object,
        )

        if self._load_etl_output:
            logger.info(f"Retrieving etl output for {submission_id=}")
            etl_outputs = {
                document: await etloutput.load_async(
                    document.etl_output_url,
                    reader=self._retrieve_storage_object,
                    text=self._load_text,
                    tokens=self._load_tokens,
                    tables=self._load_tables,
                )
                for document in result.documents
            }
        else:
            logger.info(f"Skipping etl output for {submission_id=}")
            etl_outputs = {}

        logger.info(f"Applying auto review for {submission_id=}")
        auto_reviewed = await self._auto_review(result, etl_outputs)

        logger.info(f"Submitting auto review for {submission_id=}")
        job = await self._client_call(
            SubmitReview(
                submission_id,
                changes=auto_reviewed.changes,
                force_complete=auto_reviewed.stp,
            )
        )
        job = await self._client_call(JobStatus(job.id))

        if job.status == "SUCCESS":
            logger.info(f"Completed auto review of {submission_id=}")
        else:
            logger.error(
                f"Submit failed for {submission_id=}: "
                f"{job.status=!r} {job.result=!r}"
            )

    async def _reap_workers(self) -> None:
        """
        Reap completed workers, releasing their slots for new tasks. Log errors for
        submissions that failed to process. Remove their submission IDs from
        `self._processing_submission_ids` to be retried.
        """
        while True:
            submission_id, worker = await self._worker_queue.get()

            try:
                await worker
            except Exception:
                logger.exception(f"Error occurred while processing {submission_id=}")

            self._processing_submission_ids.remove(submission_id)
            self._worker_slots.release()
