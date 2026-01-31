"""Pydantic models for Tax Explainer API requests and responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaxContext(BaseModel):
    """User's tax context for personalized explanations."""
    filing_status: Optional[str] = None
    has_dependents: Optional[bool] = None
    state: Optional[str] = None
    user_values: Optional[Dict[str, Any]] = None


class ExplainLineItemRequest(BaseModel):
    """Request to explain a tax form line item."""
    form_id: str = Field(..., description="Form identifier (e.g., '1040', 'Schedule A')")
    line_number: str = Field(..., description="Line number on the form")
    tax_year: int = Field(default=2024, description="Tax year")
    context: Optional[TaxContext] = None
    detail_level: str = Field(default="standard", description="brief, standard, or detailed")


class IRCCitation(BaseModel):
    """Citation to an IRC section."""
    section: str
    title: str
    subsections_cited: List[str] = []
    excerpt: str = ""
    source_path: str = ""


class TreasuryRegCitation(BaseModel):
    """Citation to a Treasury Regulation."""
    regulation: str
    title: str


class IRSPublicationRef(BaseModel):
    """Reference to an IRS Publication."""
    number: str
    title: str


class LegalBasis(BaseModel):
    """Legal basis for a tax explanation."""
    primary_irc_section: Optional[IRCCitation] = None
    related_sections: List[IRCCitation] = []
    treasury_regulations: List[TreasuryRegCitation] = []
    irs_publications: List[IRSPublicationRef] = []


class Explanation(BaseModel):
    """The explanation content."""
    summary: str
    plain_english: str
    calculation_notes: Optional[str] = None
    detail_level: str


class RelatedForm(BaseModel):
    """A related tax form."""
    form: str
    relationship: str


class ExplainLineItemResponse(BaseModel):
    """Response for a line item explanation."""
    explanation: Explanation
    legal_basis: LegalBasis
    related_forms: List[RelatedForm] = []
    metadata: Dict[str, Any] = {}


class SearchIRCRequest(BaseModel):
    """Request to search IRC sections."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, ge=1, le=50)
    include_regulations: bool = False


class IRCSearchResult(BaseModel):
    """Single IRC search result."""
    section: str
    title: str
    relevance_score: float
    snippet: str
    subsections: List[str] = []
    related_forms: List[str] = []


class SearchIRCResponse(BaseModel):
    """Response for IRC search."""
    results: List[IRCSearchResult]
    total_results: int
    query_understanding: Optional[Dict[str, Any]] = None


class FormLineInfo(BaseModel):
    """Information about a form line item."""
    label: str
    irc_sections: List[str]
    description: str = ""


class FormCrossRefResponse(BaseModel):
    """Cross-reference information for a form."""
    form: str
    title: str
    lines: Dict[str, FormLineInfo] = {}
    schedules: List[str] = []


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    """Request for conversational tax help."""
    messages: List[ChatMessage]
    context: Optional[TaxContext] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response for conversational tax help."""
    response: ChatMessage
    citations: List[IRCCitation] = []
    follow_up_suggestions: List[str] = []
    session_id: str
