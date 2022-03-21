from typing import Any, NamedTuple

class FKImageItem(NamedTuple):
    url: str
    name: str or callable
    meta: dict = None
    pinMeta: dict = None

class FKTaskItem(NamedTuple):
    image: Any
    baseSavePath: str

class FKWorkerTask(NamedTuple):
    kwargs: dict = None
    args: tuple = None