"""FastAPI routes for document processing and import services."""

import base64
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ..services.ocr_service import TaxDocumentOCR, DocumentScanResult, DocumentType
from ..services.brokerage_import_service import (
    BrokerageCSVImporter,
    BrokerageImportResult,
    BrokerageType,
    CostBasisTracker
)

router = APIRouter(prefix="/v1/documents", tags=["Document Processing"])

# Initialize services
ocr_service = TaxDocumentOCR()
brokerage_importer = BrokerageCSVImporter()
cost_basis_tracker = CostBasisTracker()


# Request/Response Models
class DocumentScanRequest(BaseModel):
    """Request to scan a tax document image."""
    image_base64: str
    enhance_with_vision: bool = False


class DocumentScanResponse(BaseModel):
    """Response from document scanning."""
    document_type: str
    document_year: Optional[str]
    payer_name: Optional[str]
    payer_ein: Optional[str]
    recipient_name: Optional[str]
    recipient_tin: Optional[str]
    fields: List[dict]
    confidence_score: float
    warnings: List[str]
    form_mapping: dict


class BrokerageImportRequest(BaseModel):
    """Request to import brokerage CSV data."""
    csv_content: str
    brokerage_type: Optional[str] = None
    tax_year: int = 2025


class BrokerageImportResponse(BaseModel):
    """Response from brokerage import."""
    brokerage_type: str
    transaction_count: int
    total_proceeds: str
    total_cost_basis: str
    total_gain_or_loss: str
    short_term_gain_or_loss: str
    long_term_gain_or_loss: str
    wash_sale_adjustments: str
    warnings: List[str]
    errors: List[str]
    form_8949_data: dict
    schedule_d_data: dict


class CostBasisPurchaseRequest(BaseModel):
    """Record a purchase for cost basis tracking."""
    symbol: str
    quantity: float
    price_per_share: float
    date: str  # ISO format
    fees: float = 0.0


class CostBasisSaleRequest(BaseModel):
    """Calculate cost basis for a sale."""
    symbol: str
    quantity: float
    date_sold: str  # ISO format
    method: str = "FIFO"


class WhatIfScenarioRequest(BaseModel):
    """Request for what-if tax scenario analysis."""
    current_facts: dict
    scenario_changes: List[dict]  # List of {fact_path, new_value}


class WhatIfScenarioResponse(BaseModel):
    """Response with scenario comparison."""
    current_tax: float
    scenario_tax: float
    difference: float
    affected_facts: List[dict]
    recommendations: List[str]


# ============== Document Scanning Routes ==============

@router.post("/scan/image", response_model=DocumentScanResponse)
async def scan_document_image(request: DocumentScanRequest):
    """Scan a tax document image and extract data.

    Uses OCR to extract form fields from W-2s, 1099s, etc.
    Optionally uses Claude Vision for enhanced accuracy.

    Args:
        request: Base64-encoded image and options.

    Returns:
        Extracted document data with field mappings.
    """
    try:
        result = ocr_service.scan_image(image_base64=request.image_base64)

        if request.enhance_with_vision:
            result = ocr_service.enhance_with_claude_vision(
                request.image_base64, result
            )

        return DocumentScanResponse(
            document_type=result.document_type.value,
            document_year=result.document_year,
            payer_name=result.payer_name,
            payer_ein=result.payer_ein,
            recipient_name=result.recipient_name,
            recipient_tin=result.recipient_tin,
            fields=[
                {
                    "field_name": f.field_name,
                    "value": f.value,
                    "confidence": f.confidence,
                    "form_line": f.form_line
                }
                for f in result.fields
            ],
            confidence_score=result.confidence_score,
            warnings=result.warnings,
            form_mapping=result.form_mapping
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/upload")
async def scan_uploaded_document(
    file: UploadFile = File(...),
    enhance_with_vision: bool = Form(False)
):
    """Upload and scan a tax document.

    Accepts image files (PNG, JPG) or PDF documents.

    Args:
        file: Uploaded document file.
        enhance_with_vision: Use Claude Vision for enhanced accuracy.

    Returns:
        Extracted document data.
    """
    try:
        content = await file.read()

        if file.filename.lower().endswith('.pdf'):
            results = ocr_service.scan_pdf(pdf_bytes=content)
            return [
                DocumentScanResponse(
                    document_type=r.document_type.value,
                    document_year=r.document_year,
                    payer_name=r.payer_name,
                    payer_ein=r.payer_ein,
                    recipient_name=r.recipient_name,
                    recipient_tin=r.recipient_tin,
                    fields=[
                        {
                            "field_name": f.field_name,
                            "value": f.value,
                            "confidence": f.confidence,
                            "form_line": f.form_line
                        }
                        for f in r.fields
                    ],
                    confidence_score=r.confidence_score,
                    warnings=r.warnings,
                    form_mapping=r.form_mapping
                )
                for r in results
            ]
        else:
            result = ocr_service.scan_image(image_bytes=content)
            if enhance_with_vision:
                image_b64 = base64.b64encode(content).decode('utf-8')
                result = ocr_service.enhance_with_claude_vision(image_b64, result)

            return DocumentScanResponse(
                document_type=result.document_type.value,
                document_year=result.document_year,
                payer_name=result.payer_name,
                payer_ein=result.payer_ein,
                recipient_name=result.recipient_name,
                recipient_tin=result.recipient_tin,
                fields=[
                    {
                        "field_name": f.field_name,
                        "value": f.value,
                        "confidence": f.confidence,
                        "form_line": f.form_line
                    }
                    for f in result.fields
                ],
                confidence_score=result.confidence_score,
                warnings=result.warnings,
                form_mapping=result.form_mapping
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Brokerage Import Routes ==============

@router.post("/brokerage/import", response_model=BrokerageImportResponse)
async def import_brokerage_csv(request: BrokerageImportRequest):
    """Import brokerage CSV for Form 8949 and Schedule D.

    Supports major brokerages: TD Ameritrade, Schwab, Fidelity,
    Vanguard, Robinhood, E*Trade, Interactive Brokers.

    Args:
        request: CSV content and options.

    Returns:
        Parsed transactions with Form 8949/Schedule D data.
    """
    try:
        brokerage_type = None
        if request.brokerage_type:
            brokerage_type = BrokerageType(request.brokerage_type)

        result = brokerage_importer.import_csv(
            request.csv_content,
            brokerage_type,
            request.tax_year
        )

        return BrokerageImportResponse(
            brokerage_type=result.brokerage_type.value,
            transaction_count=len(result.transactions),
            total_proceeds=str(result.total_proceeds),
            total_cost_basis=str(result.total_cost_basis),
            total_gain_or_loss=str(result.total_gain_or_loss),
            short_term_gain_or_loss=str(result.short_term_gain_or_loss),
            long_term_gain_or_loss=str(result.long_term_gain_or_loss),
            wash_sale_adjustments=str(result.wash_sale_adjustments),
            warnings=result.warnings,
            errors=result.errors,
            form_8949_data=result.form_8949_data,
            schedule_d_data=result.schedule_d_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brokerage/upload")
async def upload_brokerage_csv(
    file: UploadFile = File(...),
    brokerage_type: Optional[str] = Form(None),
    tax_year: int = Form(2025)
):
    """Upload brokerage CSV file for import.

    Args:
        file: CSV file from brokerage.
        brokerage_type: Optional brokerage identifier.
        tax_year: Tax year to filter transactions.

    Returns:
        Parsed transactions with Form 8949/Schedule D data.
    """
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')

        broker_type = BrokerageType(brokerage_type) if brokerage_type else None
        result = brokerage_importer.import_csv(csv_content, broker_type, tax_year)

        return BrokerageImportResponse(
            brokerage_type=result.brokerage_type.value,
            transaction_count=len(result.transactions),
            total_proceeds=str(result.total_proceeds),
            total_cost_basis=str(result.total_cost_basis),
            total_gain_or_loss=str(result.total_gain_or_loss),
            short_term_gain_or_loss=str(result.short_term_gain_or_loss),
            long_term_gain_or_loss=str(result.long_term_gain_or_loss),
            wash_sale_adjustments=str(result.wash_sale_adjustments),
            warnings=result.warnings,
            errors=result.errors,
            form_8949_data=result.form_8949_data,
            schedule_d_data=result.schedule_d_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Cost Basis Tracking Routes ==============

@router.post("/costbasis/purchase")
async def record_purchase(request: CostBasisPurchaseRequest):
    """Record a purchase for cost basis tracking."""
    from datetime import datetime
    from decimal import Decimal

    try:
        cost_basis_tracker.add_purchase(
            symbol=request.symbol.upper(),
            quantity=Decimal(str(request.quantity)),
            price_per_share=Decimal(str(request.price_per_share)),
            date=datetime.fromisoformat(request.date),
            fees=Decimal(str(request.fees))
        )
        return {"status": "recorded", "symbol": request.symbol.upper()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costbasis/sale")
async def calculate_sale_basis(request: CostBasisSaleRequest):
    """Calculate cost basis for a sale."""
    from datetime import datetime
    from decimal import Decimal

    try:
        total_basis, lots_used = cost_basis_tracker.calculate_cost_basis(
            symbol=request.symbol.upper(),
            quantity=Decimal(str(request.quantity)),
            date_sold=datetime.fromisoformat(request.date_sold),
            method=request.method
        )
        return {
            "symbol": request.symbol.upper(),
            "quantity_sold": request.quantity,
            "cost_basis": str(total_basis),
            "method": request.method,
            "lots_used": lots_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costbasis/holdings")
async def get_holdings(symbol: Optional[str] = None):
    """Get current holdings summary."""
    try:
        return cost_basis_tracker.get_holdings_summary(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== What-If Scenario Routes ==============

@router.post("/whatif/analyze", response_model=WhatIfScenarioResponse)
async def analyze_whatif_scenario(request: WhatIfScenarioRequest):
    """Analyze what-if tax scenarios.

    Compare current tax situation with hypothetical changes like:
    - "What if I contribute more to my IRA?"
    - "What if I sell these stocks?"
    - "What if I increase withholding?"

    Args:
        request: Current facts and proposed changes.

    Returns:
        Tax impact comparison and recommendations.
    """
    # This would integrate with the fact graph calculation engine
    # For now, return a placeholder response
    current_tax = request.current_facts.get("totalTax", 0)
    scenario_tax = current_tax  # Would recalculate based on changes

    return WhatIfScenarioResponse(
        current_tax=current_tax,
        scenario_tax=scenario_tax,
        difference=scenario_tax - current_tax,
        affected_facts=[],
        recommendations=[
            "Consider maximizing IRA contributions to reduce taxable income.",
            "Review estimated tax payments to avoid underpayment penalties."
        ]
    )


# ============== Supported Document Types ==============

@router.get("/supported-types")
async def get_supported_document_types():
    """Get list of supported tax document types for scanning."""
    return {
        "document_types": [dt.value for dt in DocumentType],
        "brokerage_types": [bt.value for bt in BrokerageType],
        "cost_basis_methods": ["FIFO", "LIFO", "SpecificID", "AverageCost"]
    }
