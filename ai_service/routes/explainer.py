"""FastAPI routes for the Tax Explainer API."""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    ExplainLineItemRequest,
    ExplainLineItemResponse,
    SearchIRCRequest,
    SearchIRCResponse,
    FormCrossRefResponse,
    ChatRequest,
    ChatResponse,
)
from ..services.tax_explainer_service import TaxExplainerService

router = APIRouter(prefix="/v1", tags=["Tax Explainer"])

# Initialize the service
# Paths are relative to the main project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # taxes/
DOCS_PATH = PROJECT_ROOT / "docs"

service = TaxExplainerService(
    irc_base_path=DOCS_PATH / "tax-law" / "irc",
    crossref_path=DOCS_PATH / "tax-law" / "_data" / "tax-crossref.json",
    direct_file_mapping_path=DOCS_PATH / "tax-law" / "_data" / "direct-file-irc-mapping.json"
)


@router.post("/explain/line-item", response_model=ExplainLineItemResponse)
async def explain_line_item(request: ExplainLineItemRequest):
    """Explain a tax form line item.

    Provides a plain-English explanation with citations to IRC sections
    and Treasury Regulations.

    Args:
        request: The explanation request containing form ID, line number, etc.

    Returns:
        Detailed explanation with legal basis and related information.
    """
    try:
        return service.explain_line_item(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/irc", response_model=SearchIRCResponse)
async def search_irc(request: SearchIRCRequest):
    """Search IRC sections by keyword.

    Performs a semantic search over IRC sections and returns
    relevant results with snippets.

    Args:
        request: Search query and filters.

    Returns:
        List of matching IRC sections with relevance scores.
    """
    try:
        return service.search_irc(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crossref/form/{form_id}", response_model=FormCrossRefResponse)
async def get_form_crossref(form_id: str):
    """Get cross-reference data for a tax form.

    Returns IRC sections, regulations, and publications
    related to each line item on the form.

    Args:
        form_id: The form identifier (e.g., "1040", "Schedule A").

    Returns:
        Cross-reference mapping for the form.
    """
    try:
        return service.get_form_crossref(form_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Conversational tax assistance.

    Provides multi-turn conversational help for tax questions.
    Maintains session state for follow-up questions.

    Args:
        request: Chat messages and optional session ID.

    Returns:
        Assistant response with citations and follow-up suggestions.
    """
    try:
        return service.chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
