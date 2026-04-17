from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from .spinner import run_with_spinner

F = TypeVar("F", bound=Callable[..., Any])


def command(*, long_running: bool = False) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        if not long_running:
            return fn

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            json_mode = kwargs.get("json") or kwargs.get("json_", False)
            if json_mode:
                return fn(*args, **kwargs)
            label = fn.__name__.replace("_", " ")
            return run_with_spinner(lambda: fn(*args, **kwargs), label=label)

        return wrapper  # type: ignore[return-value]

    return decorator
