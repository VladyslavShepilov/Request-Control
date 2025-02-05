from typing import Callable, Any
from datetime import datetime, timedelta
import inspect
from threading import Lock
from contextlib import contextmanager
from functools import wraps
from asyncio import iscoroutinefunction


class KeywordSingleton(type):
    """
    Ensures only one instance per specified target.
    """
    __instances: dict = {}

    def __call__(cls, *args, target=None, **kwargs):
        if target not in cls.__instances:
            kwargs["target"] = target
            cls.__instances[target] = super().__call__(*args, **kwargs)
        return cls.__instances[target]


class IntervalTrackerMixin:
    """
    Tracks actions over a specified interval.
    """

    class Interval:
        def __init__(self, duration: int, limit: int):
            self.duration = timedelta(seconds=duration)
            self.limit = limit

        def __str__(self):
            return f"{self.limit} / {str(self.duration)}"

    def __init__(self, duration: int, limit: int, execution_time: int = 10):
        """
        Sets throttling interval.
        Optionally 'execution_time' to match throttling exactly.
        """
        self.interval = self.Interval(duration, limit)
        self._execution_time: timedelta = timedelta(milliseconds=execution_time)
        self.actions_counter: int = 0
        self.interval_start: datetime | None = None
        self.interval_end: datetime | None = None
        self.lock = Lock()

    def refresh_timers(self, submit_time: datetime):
        """Resets the interval tracking."""
        self.interval_start = submit_time
        self.interval_end = submit_time + self.interval.duration
        self.actions_counter = 0

    def now_execution_time(self) -> tuple[datetime, datetime]:
        """Gets the current time and estimated execution time."""
        now = datetime.now()
        submit_time = now + self._execution_time
        return now, submit_time

    def make_request(self) -> bool:
        """Checks if a request can be made within the interval limit."""
        now, submit_time = self.now_execution_time()

        with self.lock:
            if not self.interval_start or now > self.interval_end:
                self.refresh_timers(submit_time)
                self.actions_counter += 1
                return True

            if self.interval_start <= now <= self.interval_end:
                if self.actions_counter < self.interval.limit:
                    self.actions_counter += 1
                    return True
                return False

        return False


class ThrottlerDecorator(IntervalTrackerMixin, metaclass=KeywordSingleton):
    def __init__(self, duration: int, limit: int, target: Any = None):
        super().__init__(duration, limit)  # Use super() instead of direct Mixin init
        self.target = target

    def __call__(self, obj: Any) -> Any:
        """Handles proper decorator invocation."""
        if inspect.isclass(obj):
            return self._decorate_class(obj)
        if inspect.isfunction(obj) or iscoroutinefunction(obj):
            return self._decorate_func(obj)
        raise ValueError("Invalid decorated type")

    def _decorate_func(self, func: Callable) -> Callable:
        """Wraps a function to enforce throttling."""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with self.throttling_context():
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with self.throttling_context():
                return func(*args, **kwargs)

        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    def _decorate_class(self, cls: type) -> type:
        """Wraps all methods of a class except magic methods."""
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("__"):
                setattr(cls, name, self._decorate_func(func))
        return cls

    @contextmanager
    def throttling_context(self):
        """Context manager to handle request throttling."""
        if self.make_request():
            yield
        else:
            raise RuntimeError("Request throttled due to exceeding limit")
