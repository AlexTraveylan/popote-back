from datetime import date
from typing import Annotated

from fastapi import Depends, Query

from src.container import Container, get_container


def today_or(on: Annotated[date | None, Query()] = None) -> date:
    return on or date.today()  # noqa: DTZ011


ContainerDep = Annotated[Container, Depends(get_container)]
DayDep = Annotated[date, Depends(today_or)]
