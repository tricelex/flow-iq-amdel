import json
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import Form
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def form_as_model(model_class: type[T]) -> Callable[..., T]:
    """Factory that returns a dependency for parsing a form field containing JSON
    into the given Pydantic model.
    """

    def _as_model(data: str = Form(...)) -> T:
        return model_class(**json.loads(data))

    return _as_model


def format_sse(data: Any, event: str | None = None) -> str:
    """Format data as a Server-Sent Event"""
    message = f"data: {json.dumps(data)}\n"
    if event:
        message = f"event: {event}\n{message}"
    return f"{message}\n"
