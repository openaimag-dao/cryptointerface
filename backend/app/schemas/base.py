from pydantic import BaseModel, ConfigDict


def to_camel(snake_str: str) -> str:
    first, *rest = snake_str.split("_")
    return first + "".join(word.capitalize() for word in rest)


class CamelModel(BaseModel):
    """Base for schemas exposed to the frontend: Python stays snake_case
    internally, JSON on the wire is camelCase (idiomatic on both sides).
    FastAPI serializes by alias by default, so this needs no per-route config.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
