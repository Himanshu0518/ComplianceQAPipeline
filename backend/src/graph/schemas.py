
# Pydantic
from pydantic import BaseModel, Field
from typing import Optional,List

class ComplianceIssueOutput(BaseModel):
    """A single brand-safety violation found in the video."""
    category: str = Field(description="Category of the violation, e.g. 'Claim Violation', 'Prohibited Content'")
    description: str = Field(description="Detailed description of the violation")
    severity: str = Field(description="Severity level: HIGH, MEDIUM, or LOW")
    timestamp: Optional[str] = Field(default=None, description="Approximate timestamp in the video, if identifiable")


class AuditResult(BaseModel):
    """Full compliance audit result returned by the LLM."""
    compliance_results: List[ComplianceIssueOutput] = Field(
        default_factory=list,
        description="List of all compliance violations found. Empty list if the video passes."
    )
    final_status: str = Field(description="Overall verdict: PASS or FAIL")
    final_report: str = Field(description="Markdown-formatted summary of audit findings")
