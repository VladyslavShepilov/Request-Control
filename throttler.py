from typing import Callable, Any
from datetime import datetime, timedelta
import inspect
from threading import Lock


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
    Tracks actions over a specified interval to enforce throttling.
    """

    class Interval:
        def __init__(self, duration: int, limit: int):
            self.duration = timedelta(seconds=duration)
            self.limit = limit

        def __str__(self):
            return f"{self.limit} / {str(self.duration)}"

    def __init__(self, duration: int, limit: int):
        self.interval = self.Interval(duration, limit)
        self.actions_counter: int = 0
        self.interval_start: datetime | None = None
        self.interval_end: datetime | None = None
        self.lock = Lock()

    def refresh_timers(self, submit_time: datetime):
        """Resets the interval tracking."""
        self.interval_start = submit_time
        self.interval_end = submit_time + self.interval.duration
        self.actions_counter = 0

    @staticmethod
    def now_execution_time() -> tuple[datetime, datetime]:
        """Gets the current time and estimated execution time."""
        execution_time = timedelta(seconds=1)  # TODO - Should be configurable
        now = datetime.now()
        submit_time = now + execution_time
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
        IntervalTrackerMixin.__init__(self, duration, limit)
        self.target = target

    def __call__(self, class_or_func):
        """Handles proper decorator invocation."""
        if inspect.isclass(class_or_func):
            return self._decorate_class(class_or_func)
        elif inspect.isfunction(class_or_func):
            return self._decorate_func(class_or_func)
        else:
            raise ValueError("Invalid decorated type")

    def _decorate_func(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if self.make_request():
                return func(*args, **kwargs)
            else:
                raise RuntimeError("Request throttled due to exceeding limit")
        return wrapper

    def _decorate_class(self, cls) -> type:
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("__"):
                setattr(cls, name, self._decorate_func(func))
        return cls
