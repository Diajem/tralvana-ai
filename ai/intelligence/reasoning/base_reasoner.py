from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ai.intelligence.knowledge.knowledge_service import KnowledgeService


@dataclass
class ReasoningResult:
    """
    Consistent output contract for all TravelOS reasoners.

    Every field is serialisable so results can be passed directly to
    agents as AgentResult.data or returned from API endpoints.
    """
    reasoner_name: str
    subject: str                                   # destination / city / traveller_id
    success: bool
    confidence: float                              # 0.0–1.0
    data: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    reasoning_source: str = "knowledge_graph_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseReasoner(ABC):
    """
    Abstract base for all TravelOS reasoning services.

    Each subclass must implement `reason(**kwargs) -> ReasoningResult`.
    The constructor accepts an optional KnowledgeService for dependency
    injection (testing / alternative graph backends).
    """

    def __init__(self, knowledge_service: KnowledgeService | None = None) -> None:
        if knowledge_service is not None:
            self._ks = knowledge_service
        else:
            # Lazy import avoids circular dependency at module load time
            from ai.intelligence import knowledge_service as _default_ks
            self._ks = _default_ks

    @abstractmethod
    def reason(self, **kwargs: Any) -> ReasoningResult:
        ...

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _not_found(self, subject: str, message: str) -> ReasoningResult:
        return ReasoningResult(
            reasoner_name=self.__class__.__name__,
            subject=subject,
            success=False,
            confidence=0.0,
            data={"message": message},
            limitations=[f"'{subject}' not found in knowledge graph"],
        )

    def _city_and_country(self, destination: str) -> tuple[Any, Any] | tuple[None, None]:
        """Return (city_node, country_node) or (None, None) if not found."""
        city = self._ks.find_entity("City", destination)
        if city is None:
            return None, None
        country = self._ks.find_entity_by_id(city.country_id)
        return city, country
