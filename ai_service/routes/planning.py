"""FastAPI routes for tax planning, interview wizard, and notifications."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.prior_year_import_service import (
    PriorYearImportService,
    ImportSource,
    CarryForwardField
)
from ..services.interview_wizard_service import (
    InterviewWizardService,
    InterviewState,
    InterviewProgress,
    QuestionCategory
)
from ..services.tax_planning_service import (
    TaxPlanningService,
    FilingStatus,
    TaxCalculation,
    TaxPlanningRecommendation
)
from ..services.push_notification_service import (
    PushNotificationService,
    NotificationType,
    NotificationPriority
)

router = APIRouter(prefix="/v1/planning", tags=["Tax Planning"])

# Initialize services
prior_year_service = PriorYearImportService()
interview_service = InterviewWizardService()
tax_planning_service = TaxPlanningService()
notification_service = PushNotificationService()


# ============== Request/Response Models ==============

class PriorYearImportRequest(BaseModel):
    """Request to import prior year data."""
    json_content: Optional[str] = None
    transcript_text: Optional[str] = None
    source_type: str = "json_export"


class PriorYearImportResponse(BaseModel):
    """Response from prior year import."""
    success: bool
    source: str
    tax_year: Optional[int]
    carry_forward_fields: List[dict]
    warnings: List[str]
    errors: List[str]


class ApplyCarryForwardRequest(BaseModel):
    """Request to apply carry-forward fields."""
    current_facts: Dict[str, Any]
    field_paths: Optional[List[str]] = None


class InterviewAnswerRequest(BaseModel):
    """Request to submit an interview answer."""
    session_id: str
    answer: Any


class InterviewStateResponse(BaseModel):
    """Response with current interview state."""
    session_id: str
    current_question: Optional[dict]
    progress: dict
    is_complete: bool
    errors: Dict[str, str]


class TaxCalculationRequest(BaseModel):
    """Request for tax calculation."""
    facts: Dict[str, Any]
    filing_status: str = "single"


class TaxCalculationResponse(BaseModel):
    """Response with tax calculation."""
    gross_income: str
    adjusted_gross_income: str
    taxable_income: str
    total_tax: str
    refund_or_owed: str
    marginal_rate: str
    effective_rate: str
    breakdown: dict


class WhatIfRequest(BaseModel):
    """Request for what-if scenario analysis."""
    facts: Dict[str, Any]
    changes: Dict[str, Any]
    filing_status: str = "single"
    scenario_name: str = "Custom Scenario"


class WhatIfResponse(BaseModel):
    """Response with what-if analysis."""
    original_tax: str
    new_tax: str
    difference: str
    savings_or_cost: str
    recommendations: List[str]


class PushSubscriptionRequest(BaseModel):
    """Request to register push subscription."""
    user_id: str
    endpoint: str
    p256dh: str
    auth: str
    device_info: Optional[str] = None


class NotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    user_id: str
    enabled: Optional[bool] = None
    estimated_tax_reminders: Optional[bool] = None
    filing_deadline_reminders: Optional[bool] = None
    document_notifications: Optional[bool] = None
    refund_status: Optional[bool] = None
    tax_tips: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    advance_days: Optional[int] = None


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    user_id: str
    title: str
    body: str
    notification_type: str = "system"
    priority: str = "normal"
    data: Optional[Dict[str, Any]] = None


# ============== Interview Session Storage ==============

interview_sessions: Dict[str, InterviewState] = {}


# ============== Prior Year Import Routes ==============

@router.post("/import/prior-year", response_model=PriorYearImportResponse)
async def import_prior_year(request: PriorYearImportRequest):
    """Import prior year tax return data.

    Supports JSON export format and IRS transcript text.
    Returns carry-forward fields that can be applied to current year.
    """
    try:
        if request.json_content:
            result = prior_year_service.import_json(request.json_content)
        elif request.transcript_text:
            result = prior_year_service.import_irs_transcript(request.transcript_text)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either json_content or transcript_text is required"
            )

        return PriorYearImportResponse(
            success=result.success,
            source=result.source.value,
            tax_year=result.prior_year_data.tax_year if result.prior_year_data else None,
            carry_forward_fields=[
                {
                    "field_path": f.field_path,
                    "field_name": f.field_name,
                    "prior_value": str(f.prior_value),
                    "suggested_value": str(f.suggested_value) if f.carry_forward_type != "reference" else None,
                    "carry_forward_type": f.carry_forward_type,
                    "confidence": f.confidence,
                    "notes": f.notes
                }
                for f in result.carry_forward_fields
            ],
            warnings=result.warnings,
            errors=result.errors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/apply-carry-forward")
async def apply_carry_forward(request: ApplyCarryForwardRequest):
    """Apply carry-forward fields to current year facts.

    Args:
        request: Current facts and optional field paths to apply.

    Returns:
        Updated facts and list of applied fields.
    """
    try:
        # This would use stored carry-forward data from a previous import
        # For now, return the current facts unchanged
        return {
            "updated_facts": request.current_facts,
            "applied_fields": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Interview Wizard Routes ==============

@router.post("/interview/start", response_model=InterviewStateResponse)
async def start_interview():
    """Start a new interview session."""
    import uuid
    session_id = str(uuid.uuid4())

    state = interview_service.start_interview()
    interview_sessions[session_id] = state

    current_q = interview_service.get_current_question(state)
    progress = interview_service.get_progress(state)

    return InterviewStateResponse(
        session_id=session_id,
        current_question=_question_to_dict(current_q) if current_q else None,
        progress=_progress_to_dict(progress),
        is_complete=state.is_complete,
        errors=state.errors
    )


@router.post("/interview/answer", response_model=InterviewStateResponse)
async def submit_answer(request: InterviewAnswerRequest):
    """Submit an answer to the current interview question."""
    if request.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")

    state = interview_sessions[request.session_id]
    state = interview_service.answer_question(state, request.answer)
    interview_sessions[request.session_id] = state

    current_q = interview_service.get_current_question(state)
    progress = interview_service.get_progress(state)

    return InterviewStateResponse(
        session_id=request.session_id,
        current_question=_question_to_dict(current_q) if current_q else None,
        progress=_progress_to_dict(progress),
        is_complete=state.is_complete,
        errors=state.errors
    )


@router.post("/interview/back", response_model=InterviewStateResponse)
async def go_back(session_id: str):
    """Go back to the previous question."""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")

    state = interview_sessions[session_id]
    state = interview_service.go_back(state)
    interview_sessions[session_id] = state

    current_q = interview_service.get_current_question(state)
    progress = interview_service.get_progress(state)

    return InterviewStateResponse(
        session_id=session_id,
        current_question=_question_to_dict(current_q) if current_q else None,
        progress=_progress_to_dict(progress),
        is_complete=state.is_complete,
        errors=state.errors
    )


@router.post("/interview/skip", response_model=InterviewStateResponse)
async def skip_question(session_id: str):
    """Skip the current question (if allowed)."""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")

    state = interview_sessions[session_id]
    state = interview_service.skip_question(state)
    interview_sessions[session_id] = state

    current_q = interview_service.get_current_question(state)
    progress = interview_service.get_progress(state)

    return InterviewStateResponse(
        session_id=session_id,
        current_question=_question_to_dict(current_q) if current_q else None,
        progress=_progress_to_dict(progress),
        is_complete=state.is_complete,
        errors=state.errors
    )


@router.get("/interview/{session_id}/facts")
async def get_interview_facts(session_id: str):
    """Get the fact dictionary mappings from interview answers."""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")

    state = interview_sessions[session_id]
    facts = interview_service.get_fact_mapping(state)

    return {"facts": facts, "is_complete": state.is_complete}


@router.get("/interview/categories")
async def get_interview_categories():
    """Get list of interview categories."""
    return {
        "categories": [
            {"id": cat.value, "name": cat.name.replace("_", " ").title()}
            for cat in QuestionCategory
        ]
    }


# ============== Tax Planning Routes ==============

@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax(request: TaxCalculationRequest):
    """Calculate tax based on provided facts."""
    try:
        filing_status = FilingStatus(request.filing_status)
    except ValueError:
        filing_status = FilingStatus.SINGLE

    try:
        calc = tax_planning_service.calculate_tax(request.facts, filing_status)

        return TaxCalculationResponse(
            gross_income=f"${calc.gross_income:,.2f}",
            adjusted_gross_income=f"${calc.adjusted_gross_income:,.2f}",
            taxable_income=f"${calc.taxable_income:,.2f}",
            total_tax=f"${calc.total_tax:,.2f}",
            refund_or_owed=f"${abs(calc.refund_or_owed):,.2f} {'refund' if calc.refund_or_owed > 0 else 'owed'}",
            marginal_rate=f"{calc.marginal_rate}%",
            effective_rate=f"{calc.effective_rate}%",
            breakdown={
                "regular_tax": float(calc.regular_tax),
                "self_employment_tax": float(calc.self_employment_tax),
                "niit": float(calc.niit),
                "credits": float(calc.total_credits),
                "withholding": float(calc.withholding),
                "estimated_payments": float(calc.estimated_payments),
                "deduction_used": calc.deduction_used,
                "standard_deduction": float(calc.standard_deduction),
                "itemized_deduction": float(calc.itemized_deduction)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatif", response_model=WhatIfResponse)
async def analyze_whatif(request: WhatIfRequest):
    """Analyze a what-if tax scenario."""
    try:
        filing_status = FilingStatus(request.filing_status)
    except ValueError:
        filing_status = FilingStatus.SINGLE

    try:
        scenario = tax_planning_service.analyze_scenario(
            request.facts,
            request.changes,
            filing_status,
            request.scenario_name
        )

        diff = scenario.tax_difference
        savings_or_cost = f"{'Save' if diff < 0 else 'Cost'} ${abs(diff):,.2f}"

        return WhatIfResponse(
            original_tax=f"${scenario.original_calculation.total_tax:,.2f}",
            new_tax=f"${scenario.new_calculation.total_tax:,.2f}",
            difference=f"${diff:,.2f}",
            savings_or_cost=savings_or_cost,
            recommendations=scenario.recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations")
async def get_recommendations(request: TaxCalculationRequest):
    """Get tax planning recommendations."""
    try:
        filing_status = FilingStatus(request.filing_status)
    except ValueError:
        filing_status = FilingStatus.SINGLE

    try:
        recs = tax_planning_service.get_planning_recommendations(
            request.facts, filing_status
        )

        return {
            "recommendations": [
                {
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "potential_savings": f"${r.potential_savings:,.2f}",
                    "action_items": r.action_items,
                    "priority": r.priority
                }
                for r in recs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marginal-impact")
async def calculate_marginal_impact(
    facts: Dict[str, Any],
    additional_income: float,
    filing_status: str = "single"
):
    """Calculate the tax impact of additional income."""
    try:
        fs = FilingStatus(filing_status)
    except ValueError:
        fs = FilingStatus.SINGLE

    from decimal import Decimal
    result = tax_planning_service.calculate_marginal_impact(
        facts, fs, Decimal(str(additional_income))
    )

    return {
        "additional_income": f"${result['additional_income']:,.2f}",
        "additional_tax": f"${result['additional_tax']:,.2f}",
        "take_home": f"${result['take_home']:,.2f}",
        "marginal_rate": f"{result['marginal_rate']}%",
        "new_bracket": f"{result['new_bracket']}%",
        "bracket_changed": result['bracket_changed']
    }


# ============== Notification Routes ==============

@router.post("/notifications/subscribe")
async def subscribe_to_notifications(request: PushSubscriptionRequest):
    """Register for push notifications."""
    try:
        subscription = notification_service.register_subscription(
            user_id=request.user_id,
            endpoint=request.endpoint,
            p256dh=request.p256dh,
            auth=request.auth,
            device_info=request.device_info
        )

        return {
            "status": "subscribed",
            "user_id": subscription.user_id,
            "created_at": subscription.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/unsubscribe")
async def unsubscribe_from_notifications(user_id: str, endpoint: str):
    """Unsubscribe from push notifications."""
    result = notification_service.unregister_subscription(user_id, endpoint)
    return {"status": "unsubscribed" if result else "not_found"}


@router.put("/notifications/preferences")
async def update_notification_preferences(request: NotificationPreferencesRequest):
    """Update notification preferences."""
    prefs_dict = request.dict(exclude_none=True, exclude={"user_id"})

    prefs = notification_service.update_preferences(request.user_id, prefs_dict)

    return {
        "user_id": prefs.user_id,
        "enabled": prefs.enabled,
        "estimated_tax_reminders": prefs.estimated_tax_reminders,
        "filing_deadline_reminders": prefs.filing_deadline_reminders,
        "document_notifications": prefs.document_notifications,
        "refund_status": prefs.refund_status,
        "tax_tips": prefs.tax_tips,
        "quiet_hours_start": prefs.quiet_hours_start,
        "quiet_hours_end": prefs.quiet_hours_end,
        "advance_days": prefs.advance_days
    }


@router.get("/notifications/preferences/{user_id}")
async def get_notification_preferences(user_id: str):
    """Get notification preferences for a user."""
    prefs = notification_service.get_preferences(user_id)

    return {
        "user_id": prefs.user_id,
        "enabled": prefs.enabled,
        "estimated_tax_reminders": prefs.estimated_tax_reminders,
        "filing_deadline_reminders": prefs.filing_deadline_reminders,
        "document_notifications": prefs.document_notifications,
        "refund_status": prefs.refund_status,
        "tax_tips": prefs.tax_tips,
        "quiet_hours_start": prefs.quiet_hours_start,
        "quiet_hours_end": prefs.quiet_hours_end,
        "advance_days": prefs.advance_days
    }


@router.post("/notifications/send")
async def send_notification(request: SendNotificationRequest):
    """Send a notification to a user."""
    try:
        notification_type = NotificationType(request.notification_type)
    except ValueError:
        notification_type = NotificationType.SYSTEM

    try:
        priority = NotificationPriority(request.priority)
    except ValueError:
        priority = NotificationPriority.NORMAL

    result = await notification_service.send_notification(
        user_id=request.user_id,
        title=request.title,
        body=request.body,
        notification_type=notification_type,
        data=request.data,
        priority=priority
    )

    return result


@router.get("/notifications/upcoming/{user_id}")
async def get_upcoming_reminders(user_id: str, days: int = 30):
    """Get upcoming reminder notifications."""
    reminders = notification_service.get_upcoming_reminders(user_id, days)
    return {"reminders": reminders}


@router.get("/calendar")
async def get_tax_calendar(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get tax calendar events."""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    events = notification_service.get_tax_calendar_events(start, end)
    return {"events": events}


# ============== Helper Functions ==============

def _question_to_dict(question) -> dict:
    """Convert Question to dictionary."""
    return {
        "id": question.id,
        "type": question.question_type.value,
        "category": question.category.value,
        "text": question.text,
        "help_text": question.help_text,
        "options": [
            {
                "value": opt.value,
                "label": opt.label,
                "description": opt.description
            }
            for opt in question.options
        ],
        "default_value": question.default_value,
        "fact_path": question.fact_path
    }


def _progress_to_dict(progress: InterviewProgress) -> dict:
    """Convert InterviewProgress to dictionary."""
    return {
        "total_questions": progress.total_questions,
        "answered_questions": progress.answered_questions,
        "skipped_questions": progress.skipped_questions,
        "current_category": progress.current_category,
        "categories_complete": progress.categories_complete,
        "percent_complete": progress.percent_complete
    }
