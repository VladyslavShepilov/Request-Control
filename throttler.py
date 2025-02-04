from typing import Callable, Any
import inspect


class KeywordSingleton(type):
    __instances: dict = {}

    def __call__(cls, *args, target=None, **kwargs):
        if target not in cls.__instances.keys():
            kwargs["target"] = target
            cls.__instances[target] = super().__call__(*args, **kwargs)
        return cls.__instances[target]


class ThrottlerDecorator(metaclass=KeywordSingleton):
    def __init__(self, target: Any):
        self.target = target

    def __call__(self, class_or_func):
        if inspect.isclass(class_or_func):
            return self._decorate_class
        elif inspect.isfunction(class_or_func):
            return self._decorate_func
        else:
            raise ValueError("Invalid decorated type")

    def _decorate_func(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def _decorate_class(self, cls):
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("__"):
                setattr(cls, name, self._decorate_func(func))
        return cls
