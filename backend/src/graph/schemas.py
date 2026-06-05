from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class ComplianceIssueOutput(BaseModel):
    """A single brand-safety or regulatory violation detected in the video."""

    category: str = Field(
        description="Violation category, e.g. 'Unsubstantiated Claim', 'Missing Disclosure', 'Prohibited Content'"
    )
    description: str = Field(
        description="Specific, evidence-based description of the violation referencing the actual content"
    )
    severity: str = Field(
        description="Risk level: HIGH (legal/regulatory risk), MEDIUM (brand risk), or LOW (best-practice deviation)"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Approximate timestamp range in the video where the violation occurs, e.g. '0:12-0:18'"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Auditor confidence that this is a genuine violation, from 0.0 to 1.0"
    )
    rule_reference: Optional[str] = Field(
        default=None,
        description="The specific guideline or rule section this violation breaches, if identifiable from retrieved docs"
    )

    @field_validator("severity")
    @classmethod
    def normalise_severity(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        return max(0.0, min(1.0, v))


class AuditResult(BaseModel):
    """Complete compliance audit result produced by the LLM auditor node."""

    compliance_results: List[ComplianceIssueOutput] = Field(
        default_factory=list,
        description="All violations found. Empty list means the video passes."
    )
    final_status: str = Field(
        description="Overall verdict: PASS if no HIGH/MEDIUM violations, otherwise FAIL"
    )
    final_report: str = Field(
        description="Markdown-formatted executive summary of the audit findings"
    )
    risk_score: Optional[int] = Field(
        default=None,
        description="Aggregate risk score from 0 (clean) to 100 (critical), computed from violation severities"
    )

    @field_validator("final_status")
    @classmethod
    def normalise_status(cls, v: str) -> str:
        return v.upper().strip()
