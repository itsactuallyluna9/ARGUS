from collections import deque
from contextlib import ContextDecorator
import datetime


def utc_now():
    return datetime.datetime.now(tz=datetime.UTC)


class with_timing(ContextDecorator):
    _enter_time: datetime.datetime | None
    _exit_time: datetime.datetime | None

    def __init__(self, cb=None):
        self._enter_time = None
        self._exit_time = None
        self._cb = cb
        # self._prev_runs = deque(maxlen=7)

    def __enter__(self):
        assert self._enter_time == None

        self._enter_time = utc_now()
        self._exit_time = None

        return self

    def __exit__(self, *exc):
        self._exit_time = utc_now()
        if self._cb:
            self._cb(self)
        return self

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *exc):
        return self.__exit__(*exc)

    @property
    def duration_s(self) -> float:
        return (self._exit_time - self._enter_time).total_seconds()
