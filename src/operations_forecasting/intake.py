"""Future document-intake boundary: proposals never equal approved facts."""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ProposedOperationalRecord:
    proposal_id: str
    source_document_ref: str
    proposed_facts: tuple[tuple[str, str], ...]
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]


@dataclass(frozen=True)
class ApprovedOperationalRecord:
    record_id: str
    approved_facts: tuple[tuple[str, str], ...]
    human_decision: str
    evidence_refs: tuple[str, ...]


def admit_approved_records(records: Iterable[ApprovedOperationalRecord]) -> tuple[ApprovedOperationalRecord, ...]:
    """Boundary function for a future canonical store. Proposed records fail closed."""
    accepted = tuple(records)
    if any(type(record) is not ApprovedOperationalRecord for record in accepted):
        raise TypeError("Only human-approved operational records can enter canonical data")
    if any(record.human_decision not in {"approved", "corrected"} for record in accepted):
        raise ValueError("Canonical records need an approved or corrected human decision")
    return accepted
