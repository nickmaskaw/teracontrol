from typing import Callable, Protocol


class Queryable(Protocol):
    """Minimal protocol for querying instruments."""
    def query(self, command: str) -> str: ...


class QueryEngine:
    def __init__(
        self,
        instruments: dict[str, Queryable],
        on_response: Callable
    ):
        self.instruments = dict(instruments)
        self.on_response = on_response

    def query(self, name: str, query: str):
        response = self.instruments[name].query(query)
        self.on_response(name, query, response)