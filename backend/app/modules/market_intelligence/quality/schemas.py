from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    name: str
    status: str        # "pass" | "warn" | "fail"
    score: float       # 0.0 – 1.0
    detail: str = ""


@dataclass
class QualityResult:
    final_score: float
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.final_score >= 0.5
