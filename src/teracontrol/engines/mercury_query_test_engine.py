from typing import Callable


class MercuryQueryTestEngine:
    def __init__(self, mercury_system, on_response: Callable):
        self.mercury_system = mercury_system
        self.on_response = on_response

    def query(self, query: str):
        response = self.mercury_system.query(query)
        self.on_response(response)