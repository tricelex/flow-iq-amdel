from fastapi import Form
from pydantic import BaseModel
import json
from typing import Type, TypeVar, Callable, Any

T = TypeVar("T", bound=BaseModel)

def form_as_model(model_class: Type[T]) -> Callable[..., T]:
    """
    Factory that returns a dependency for parsing a form field containing JSON
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