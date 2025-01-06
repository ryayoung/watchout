import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
from prompt_toolkit.input import Input, create_input

@dataclass(frozen=True)
class RunDetail:
    output: str
    duration: timedelta
    timestamp: datetime
    failed: bool
    repeats: int = 0


@dataclass(frozen=True)
class Config:
    path: str
    lazy: bool
    keep_duplicates: bool
    no_watch: bool
    verbose: bool


class Global:
    config: Config
    name: str
    index: int = 0
    history: list[RunDetail] = []
    awatch_task: asyncio.Task | None = None
    done: asyncio.Event = asyncio.Event()
    input: Input = create_input()

