from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ClaimAnalysis(BaseModel):
    claim_text: str = Field(description="The specific assertion or claim evaluated.")
    status: Literal["VERIFIED", "UNVERIFIED", "CONTRADICTED"] = Field(
        description="Verification status for the claim."
    )
    confidence_score: int = Field(
        ge=0,
        le=100,
        description="Confidence score from 0 to 100 based on supporting sources.",
    )
    reasoning: str = Field(description="Detailed explanation of why this claim earned its status based strictly on search context.")
    citation_links: List[str] = Field(default_factory=list, description="URLs of search results supporting or contradicting this claim.")

class TimelineEvent(BaseModel):
    time_frame: str = Field(description="Date, year, or period of the milestone (e.g., '2021', 'August 2024', or 'Earliest Report').")
    event_title: str = Field(description="Short title describing this milestone in the claim's narrative, origin, or refutation.")
    description: str = Field(description="Explanation of what was published or reported at this point in time.")
    source_url: Optional[str] = Field(default=None, description="URL associated with this milestone if available.")

class SourceTierDistribution(BaseModel):
    tier_1_count: int = Field(ge=0, description="Count of Tier 1 sources (Government bodies, peer-reviewed journals, WHO, CDC, PubMed, Nature, official patents).")
    tier_2_count: int = Field(ge=0, description="Count of Tier 2 sources (Established mainstream news agencies like Reuters, AP, BBC, NYT, WSJ).")
    tier_3_count: int = Field(ge=0, description="Count of Tier 3 sources (Blogs, social media posts, opinion forums, unverified web portals).")
    spectrum_analysis: str = Field(description="Concise analysis of evidence distribution across tiers (e.g., '100% of Tier 1 sources refute the claim, while Tier 3 sources propagate it').")

class VeritabilityReport(BaseModel):
    headline_under_test: str = Field(description="The original viral news headline or statement analyzed.")
    overall_truth_score: int = Field(
        ge=0,
        le=100,
        description="Overall Truth Index score from 0 to 100.",
    )
    verdict_summary: str = Field(description="Concise synthesis explaining the final verdict.")
    atomic_claims: List[ClaimAnalysis] = Field(description="Detailed breakdown of each sub-claim evaluated.")
    key_sources: List[str] = Field(description="List of primary news outlets or academic sources referenced.")
    timeline: List[TimelineEvent] = Field(default_factory=list, description="Chronological timeline tracking the origin, viral spread, or official refutations of the claim.")
    source_spectrum: SourceTierDistribution = Field(description="Breakdown of source credibility across official/academic, mainstream news, and unverified web tiers.")

class HalfTruthDetail(BaseModel):
    atomic_claim: str = Field(description="The isolated sub-assertion extracted from the headline.")
    literal_truth: bool = Field(description="Is the isolated statement factually accurate on its own?")
    misleading_spin: str = Field(description="How the claim exaggerates or spins the true fact.")
    omitted_context: str = Field(description="Critical missing information that drastically alters the narrative.")
    status_label: Literal["HALF_TRUTH", "VERIFIED_TRUE", "FALSE"] = Field(
        description="Classification assigned to the isolated assertion."
    )
