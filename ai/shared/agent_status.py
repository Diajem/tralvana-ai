from enum import Enum


class AgentStatus(str, Enum):
    SUCCESS = "success"
    NEEDS_INFORMATION = "needs_information"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
