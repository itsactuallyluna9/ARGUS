from collections import deque
from contextlib import ContextDecorator
import datetime
from types import Optional


def utc_now():
    return datetime.datetime.now(tz=datetime.UTC)


class with_timing(ContextDecorator):
    _enter_time: Optional[datetime.datetime]
    _exit_time: Optional[datetime.datetime]

    def __init__(self, cb = None):
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

    @property
    def duration_s(self) -> float:
        return (self._exit_time - self._enter_time).total_seconds()
