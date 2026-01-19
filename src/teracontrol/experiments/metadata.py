import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExperimentMetadata:
    """
    Immutable experiment metadata for provenance and traceability.
    """
    experiment_id: str
    created_at_utc: str  # ISO 8601 format
    created_at_local: str  # ISO 8601 format

    operator: str
    description: Optional[str] = None
    location: Optional[str] = None

    @staticmethod
    def create(
        operator: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> ExperimentMetadata:
        now_local = datetime.now().astimezone()
        now_utc = now_local.astimezone(timezone.utc)

        return ExperimentMetadata(
            experiment_id=str(uuid.uuid4()),
            created_at_utc=now_utc.isoformat(),
            created_at_local=now_local.isoformat(),
            operator=operator,
            description=description,
            location=location,
        )