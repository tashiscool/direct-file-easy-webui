"""Core service for generating tax explanations with AI."""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

from anthropic import Anthropic

from ..retrieval.irc_retriever import IRCRetriever, RetrievalResult
from ..models.schemas import (
    ExplainLineItemRequest,
    ExplainLineItemResponse,
    Explanation,
    LegalBasis,
    IRCCitation,
    TreasuryRegCitation,
    IRSPublicationRef,
    RelatedForm,
    SearchIRCRequest,
    SearchIRCResponse,
    IRCSearchResult,
    FormCrossRefResponse,
    FormLineInfo,
    ChatRequest,
    ChatResponse,
    ChatMessage,
)

logger = logging.getLogger(__name__)


# IRC Section titles for common sections
IRC_SECTION_TITLES = {
    "1": "Tax imposed",
    "21": "Expenses for household and dependent care services",
    "22": "Credit for the elderly and the disabled",
    "24": "Child tax credit",
    "25A": "Education credits",
    "32": "Earned income",
    "36B": "Refundable credit for coverage under a qualified health plan",
    "61": "Gross income defined",
    "62": "Adjusted gross income defined",
    "63": "Taxable income defined",
    "72": "Annuities; certain proceeds of endowment and life insurance contracts",
    "83": "Property transferred in connection with performance of services",
    "86": "Social security and tier 1 railroad retirement benefits",
    "103": "Interest on state and local bonds",
    "121": "Exclusion of gain from sale of principal residence",
    "162": "Trade or business expenses",
    "163": "Interest",
    "164": "Taxes",
    "167": "Depreciation",
    "168": "Accelerated cost recovery system",
    "170": "Charitable, etc., contributions and gifts",
    "179": "Election to expense certain depreciable business assets",
    "199A": "Qualified business income",
    "213": "Medical, dental, etc., expenses",
    "219": "Retirement savings",
    "221": "Interest on education loans",
    "401": "Qualified pension, profit-sharing, and stock bonus plans",
    "408": "Individual retirement accounts",
    "469": "Passive activity losses and credits limited",
    "1001": "Determination of amount of and recognition of gain or loss",
    "1014": "Basis of property acquired from a decedent",
    "1031": "Exchange of real property held for productive use or investment",
    "1221": "Capital asset defined",
    "1222": "Other terms relating to capital gains and losses",
}

SYSTEM_PROMPT = """You are a Tax Explanation Assistant with expertise in U.S. federal income tax law.
Your role is to explain tax concepts in plain English while citing specific legal authorities.

INSTRUCTIONS:
1. Always cite specific IRC sections (e.g., "IRC Section 24(a)") for your claims
2. When citing regulations, use the format "Treas. Reg. Section 1.24-1"
3. Explain complex terms in parentheses when first used
4. Use the taxpayer's filing context (filing status, income level) to tailor explanations
5. If a concept has changed recently, note the effective date of the current rule
6. Never provide legal advice - clarify that explanations are educational
7. When uncertain, say so and suggest consulting a tax professional

RESPONSE FORMAT:
Respond with valid JSON in this exact format:
{
  "summary": "1-2 sentence summary",
  "plain_english": "Detailed explanation in plain English",
  "calculation_notes": "Any relevant calculation information (optional)",
  "primary_irc_section": "Main IRC section number (just the number like '24')",
  "related_sections": ["list", "of", "related", "section", "numbers"],
  "key_quote": "A relevant quote from the IRC section if available"
}

TAX YEAR: {tax_year}
FILING STATUS: {filing_status}
"""


class TaxExplainerService:
    """Service for generating AI-powered tax explanations."""

    def __init__(
        self,
        irc_base_path: Path,
        crossref_path: Path,
        direct_file_mapping_path: Path,
        anthropic_api_key: Optional[str] = None
    ):
        self.retriever = IRCRetriever(
            irc_base_path=irc_base_path,
            crossref_path=crossref_path,
            direct_file_mapping_path=direct_file_mapping_path
        )

        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.llm_client = Anthropic(api_key=api_key)
        else:
            self.llm_client = None
            logger.warning("No Anthropic API key provided - LLM features disabled")

    def explain_line_item(
        self,
        request: ExplainLineItemRequest
    ) -> ExplainLineItemResponse:
        """Generate an explanation for a tax form line item."""
        # Step 1: Retrieve relevant IRC content
        retrieval_result = self.retriever.retrieve_for_line_item(
            form_id=request.form_id,
            line_number=request.line_number
        )

        # Step 2: Build context from retrieval
        context = self._build_context(retrieval_result, request)

        # Step 3: Generate explanation with LLM or fallback
        if self.llm_client:
            explanation_data = self._generate_with_llm(request, context)
        else:
            explanation_data = self._generate_fallback(request, retrieval_result)

        # Step 4: Build response
        return self._build_response(
            explanation_data,
            retrieval_result,
            request
        )

    def _build_context(
        self,
        retrieval: RetrievalResult,
        request: ExplainLineItemRequest
    ) -> str:
        """Build context string from retrieval results."""
        parts = []

        for chunk in retrieval.chunks[:3]:  # Limit to top 3 chunks
            parts.append(f"=== IRC Section {chunk.section}: {chunk.title} ===")
            # Truncate content
            content = chunk.content[:2000] if len(chunk.content) > 2000 else chunk.content
            parts.append(content)
            parts.append("")

        if retrieval.crossref_data:
            parts.append("=== Cross-Reference Data ===")
            parts.append(f"Related IRC Sections: {retrieval.crossref_data.get('irc_sections', [])}")

        return "\n".join(parts)

    def _generate_with_llm(
        self,
        request: ExplainLineItemRequest,
        context: str
    ) -> Dict[str, Any]:
        """Generate explanation using Claude."""
        filing_status = "not specified"
        if request.context and request.context.filing_status:
            filing_status = request.context.filing_status

        system = SYSTEM_PROMPT.format(
            tax_year=request.tax_year,
            filing_status=filing_status
        )

        user_message = f"""Explain Form {request.form_id} Line {request.line_number} for tax year {request.tax_year}.

Detail level: {request.detail_level}

RETRIEVED CONTEXT:
{context}

Remember to respond with valid JSON only."""

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user_message}]
            )

            # Parse JSON from response
            response_text = response.content[0].text

            # Try to extract JSON
            try:
                # Look for JSON block
                if "```json" in response_text:
                    json_start = response_text.index("```json") + 7
                    json_end = response_text.index("```", json_start)
                    json_str = response_text[json_start:json_end].strip()
                elif "{" in response_text:
                    json_start = response_text.index("{")
                    json_end = response_text.rindex("}") + 1
                    json_str = response_text[json_start:json_end]
                else:
                    json_str = response_text

                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                return {
                    "summary": response_text[:200],
                    "plain_english": response_text,
                    "primary_irc_section": "",
                    "related_sections": []
                }

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback(request, None)

    def _generate_fallback(
        self,
        request: ExplainLineItemRequest,
        retrieval: Optional[RetrievalResult]
    ) -> Dict[str, Any]:
        """Generate a basic explanation without LLM."""
        sections = self.retriever.get_irc_sections_for_form_line(
            request.form_id,
            request.line_number
        )

        if sections:
            primary = sections[0]
            title = IRC_SECTION_TITLES.get(primary, "")
            return {
                "summary": f"This line relates to IRC Section {primary}" + (f" ({title})" if title else ""),
                "plain_english": f"Form {request.form_id} Line {request.line_number} is governed by Internal Revenue Code Section {primary}. Please consult IRS Publication 17 or a tax professional for detailed guidance.",
                "primary_irc_section": primary,
                "related_sections": sections[1:] if len(sections) > 1 else []
            }
        else:
            return {
                "summary": f"Form {request.form_id} Line {request.line_number}",
                "plain_english": "Please consult the form instructions or IRS Publication 17 for guidance on this line item.",
                "primary_irc_section": "",
                "related_sections": []
            }

    def _build_response(
        self,
        explanation_data: Dict[str, Any],
        retrieval: RetrievalResult,
        request: ExplainLineItemRequest
    ) -> ExplainLineItemResponse:
        """Build the full response object."""
        # Build primary IRC citation
        primary_section = explanation_data.get("primary_irc_section", "")
        primary_citation = None

        if primary_section:
            section_info = self.retriever.get_section_info(primary_section)
            primary_citation = IRCCitation(
                section=primary_section,
                title=section_info.get("heading", "") if section_info else IRC_SECTION_TITLES.get(primary_section, ""),
                subsections_cited=[],
                excerpt=explanation_data.get("key_quote", ""),
                source_path=section_info.get("path", "") if section_info else ""
            )

        # Build related sections
        related_citations = []
        for sec in explanation_data.get("related_sections", []):
            sec_info = self.retriever.get_section_info(sec)
            related_citations.append(IRCCitation(
                section=sec,
                title=sec_info.get("heading", "") if sec_info else IRC_SECTION_TITLES.get(sec, ""),
                subsections_cited=[],
                excerpt="",
                source_path=sec_info.get("path", "") if sec_info else ""
            ))

        # Get regulations and publications
        regs = []
        pubs = []
        if primary_section:
            irc_data = self.retriever.get_irc_section_data(primary_section)
            for reg in irc_data.get("regulations", [])[:3]:
                regs.append(TreasuryRegCitation(regulation=reg, title=""))
            for pub in irc_data.get("publications", [])[:3]:
                pubs.append(IRSPublicationRef(number=pub, title=""))

        # Build response
        return ExplainLineItemResponse(
            explanation=Explanation(
                summary=explanation_data.get("summary", ""),
                plain_english=explanation_data.get("plain_english", ""),
                calculation_notes=explanation_data.get("calculation_notes"),
                detail_level=request.detail_level
            ),
            legal_basis=LegalBasis(
                primary_irc_section=primary_citation,
                related_sections=related_citations,
                treasury_regulations=regs,
                irs_publications=pubs
            ),
            related_forms=[],
            metadata={
                "form_id": request.form_id,
                "line_number": request.line_number,
                "tax_year": request.tax_year
            }
        )

    def search_irc(self, request: SearchIRCRequest) -> SearchIRCResponse:
        """Search IRC sections."""
        results = self.retriever.search_sections(request.query, request.limit)

        search_results = []
        for section, score in results:
            section_info = self.retriever.get_section_info(section)
            irc_data = self.retriever.get_irc_section_data(section)

            content = self.retriever.get_section_content(section)
            snippet = content[:300] + "..." if content and len(content) > 300 else (content or "")

            search_results.append(IRCSearchResult(
                section=section,
                title=section_info.get("heading", "") if section_info else "",
                relevance_score=score,
                snippet=snippet,
                subsections=[],
                related_forms=irc_data.get("forms", []) if irc_data else []
            ))

        return SearchIRCResponse(
            results=search_results,
            total_results=len(search_results)
        )

    def get_form_crossref(self, form_id: str) -> FormCrossRefResponse:
        """Get cross-reference data for a form."""
        crossref = self.retriever.get_form_crossref(form_id)

        # Build line info from Direct File mapping
        df_mapping = self.retriever.direct_file_mapping.get("form_mappings", {}).get(form_id, {})
        fields = df_mapping.get("fields", {})

        lines = {}
        for field_id, field_data in fields.items():
            lines[field_id] = FormLineInfo(
                label=field_data.get("label", ""),
                irc_sections=field_data.get("irc_sections", []),
                description=""
            )

        return FormCrossRefResponse(
            form=form_id,
            title=df_mapping.get("title", ""),
            lines=lines,
            schedules=crossref.get("schedules", [])
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Handle conversational tax questions."""
        if not self.llm_client:
            return ChatResponse(
                response=ChatMessage(
                    role="assistant",
                    content="Chat functionality requires an API key. Please configure ANTHROPIC_API_KEY."
                ),
                citations=[],
                follow_up_suggestions=[],
                session_id=request.session_id or "no-session"
            )

        # Build system prompt for chat
        system = """You are a helpful Tax Assistant. Answer questions about U.S. federal income tax.

Always cite IRC sections when relevant. Be concise and helpful. If you're unsure, say so.
Do not provide legal or financial advice - your explanations are educational only."""

        # Convert messages
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
        ]

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system,
                messages=messages
            )

            return ChatResponse(
                response=ChatMessage(
                    role="assistant",
                    content=response.content[0].text
                ),
                citations=[],
                follow_up_suggestions=[],
                session_id=request.session_id or "new-session"
            )

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return ChatResponse(
                response=ChatMessage(
                    role="assistant",
                    content=f"I encountered an error processing your question. Please try again."
                ),
                citations=[],
                follow_up_suggestions=[],
                session_id=request.session_id or "error-session"
            )
