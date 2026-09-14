from __future__ import annotations

import time

from .embeddings import EmbeddingService, EmbeddingUnavailable
from .locking import local_lock


def run_worker(batch_size: int = 64) -> int:
    # Local exclusion limits duplicate model RAM; PostgreSQL owns correctness across machines.
    with local_lock("embedding-worker") as acquired:
        if not acquired:
            return 0
        processed, idle = 0, 0
        while idle < 2:
            try:
                result = EmbeddingService().run_pending(batch_size)
            except EmbeddingUnavailable:
                break
            count = int(result.get("processed", 0))
            processed += count
            idle = 0 if count else idle + 1
            if not count:
                time.sleep(0.5)
        return processed
