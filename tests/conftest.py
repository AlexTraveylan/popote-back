from collections.abc import Iterator

import pytest

from src.container import reset_container


@pytest.fixture(autouse=True)
def isolate_container() -> Iterator[None]:
    yield
    reset_container()
