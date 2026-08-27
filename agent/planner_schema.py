from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class SearchEngineType(str, Enum):
    GOOGLE_SEARCH = "google_search"
    GOOGLE_SCHOLAR = "google_scholar"
    GOOGLE_PATENTS = "google_patents"
    GOOGLE_NEWS = "google_news"

class SubQuery(BaseModel):
    query: str = Field(description="The exact search string to pass to the engine.")
    engine: SearchEngineType = Field(description="The target SerpApi engine best suited for this sub-query.")
    rationale: str = Field(description="Short reason why this engine and query combination was chosen.")

class ResearchPlan(BaseModel):
    objective: str = Field(description="Summary of the user's overall research target.")
    sub_queries: List[SubQuery] = Field(description="Targeted list of sub-queries (3 to 6 max).")