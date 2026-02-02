from teracontrol.core.instruments import InstrumentRegistry
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class QueryEngine:
    def __init__(
        self,
        registry: InstrumentRegistry,
    ):
        self._registry = registry

    def query(self, name: str, cmd: str):
        try:
            inst = self._registry.get(name)
            response = inst.query(cmd)
            log.info(f"Query response: {name} -> {cmd} -> {response}")
            return response
        
        except Exception:
            log.error(f"Failed to query {name}: {cmd}", exc_info=True)
            return f"Failed to query {name}: {cmd}"