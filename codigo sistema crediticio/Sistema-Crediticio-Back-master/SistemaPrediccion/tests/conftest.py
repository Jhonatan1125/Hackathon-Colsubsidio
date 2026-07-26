from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from credit_engine.database.connection import DATABASE_URL_ENV_VAR
from credit_engine.ingestion.queue import InMemoryBatchQueue, set_queue
from credit_engine.worker import service as worker_service


@pytest.fixture
def queue() -> InMemoryBatchQueue:
    return InMemoryBatchQueue()


@pytest.fixture
def client(queue: InMemoryBatchQueue, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    # Tests always run on the in-memory stand-ins, even on machines where
    # the real database URL is exported (the lifespan would wire it).
    monkeypatch.delenv(DATABASE_URL_ENV_VAR, raising=False)
    set_queue(queue)
    worker_service.reset_to_defaults()
    from credit_engine.main import app

    with TestClient(app) as test_client:
        yield test_client
