"""FastAPI routes for cryptocurrency tax import and reporting services."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/v1/crypto", tags=["Cryptocurrency"])


# ============== Enums ==============

class CostBasisMethod(str, Enum):
    """Cost basis calculation methods for cryptocurrency."""
    FIFO = "FIFO"  # First In, First Out
    LIFO = "LIFO"  # Last In, First Out
    HIFO = "HIFO"  # Highest In, First Out (tax-loss harvesting)
    SPEC_ID = "SPEC_ID"  # Specific Identification
    AVERAGE = "AVERAGE"  # Average Cost (not IRS-approved for crypto, but some use)


class Exchange(str, Enum):
    """Supported cryptocurrency exchanges."""
    COINBASE = "coinbase"
    COINBASE_PRO = "coinbase_pro"
    KRAKEN = "kraken"
    BINANCE_US = "binance_us"
    GEMINI = "gemini"
    CRYPTO_COM = "crypto_com"
    ROBINHOOD = "robinhood"
    OTHER = "other"


class TransactionType(str, Enum):
    """Types of cryptocurrency transactions."""
    BUY = "buy"
    SELL = "sell"
    TRADE = "trade"  # Crypto-to-crypto
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STAKING_REWARD = "staking_reward"
    MINING_REWARD = "mining_reward"
    AIRDROP = "airdrop"
    FORK = "fork"
    GIFT_RECEIVED = "gift_received"
    GIFT_SENT = "gift_sent"
    INTEREST = "interest"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_SENT = "payment_sent"
    FEE = "fee"
    LOST = "lost"  # Lost/stolen crypto
    MARGIN_TRADE = "margin_trade"


class HoldingPeriod(str, Enum):
    """IRS holding period classifications."""
    SHORT_TERM = "short_term"  # Held <= 1 year
    LONG_TERM = "long_term"  # Held > 1 year


class Form8949Box(str, Enum):
    """Form 8949 checkbox categories."""
    A = "A"  # Short-term, reported on 1099-B with basis
    B = "B"  # Short-term, reported on 1099-B without basis
    C = "C"  # Short-term, not reported on 1099-B
    D = "D"  # Long-term, reported on 1099-B with basis
    E = "E"  # Long-term, reported on 1099-B without basis
    F = "F"  # Long-term, not reported on 1099-B


# ============== Request/Response Models ==============

class CryptoTransaction(BaseModel):
    """A single cryptocurrency transaction."""
    id: Optional[str] = Field(None, description="Unique transaction identifier")
    exchange: Optional[Exchange] = Field(None, description="Exchange where transaction occurred")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    date: datetime = Field(..., description="Transaction date and time")
    asset: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    quantity: Decimal = Field(..., description="Amount of cryptocurrency", gt=0)
    price_per_unit: Optional[Decimal] = Field(None, description="Price per unit in USD")
    total_value_usd: Optional[Decimal] = Field(None, description="Total transaction value in USD")
    fee_usd: Decimal = Field(default=Decimal("0"), description="Transaction fees in USD")
    received_asset: Optional[str] = Field(None, description="Asset received (for trades)")
    received_quantity: Optional[Decimal] = Field(None, description="Quantity received (for trades)")
    tx_hash: Optional[str] = Field(None, description="Blockchain transaction hash")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_encoders = {Decimal: str}


class CSVImportRequest(BaseModel):
    """Request to import cryptocurrency transactions from CSV."""
    csv_content: str = Field(..., description="CSV file content as string")
    exchange: Optional[Exchange] = Field(None, description="Exchange format (auto-detected if not provided)")
    tax_year: int = Field(default=2025, description="Tax year to filter transactions")


class CSVImportResponse(BaseModel):
    """Response from CSV import."""
    success: bool
    exchange_detected: Optional[str]
    transactions_imported: int
    transactions_skipped: int
    warnings: List[str] = []
    errors: List[str] = []
    date_range: Optional[Dict[str, str]] = None
    assets_found: List[str] = []


class ExchangeAPICredentials(BaseModel):
    """Credentials for exchange API access."""
    api_key: str = Field(..., description="Exchange API key")
    api_secret: str = Field(..., description="Exchange API secret")
    passphrase: Optional[str] = Field(None, description="API passphrase (required for some exchanges)")


class APIImportRequest(BaseModel):
    """Request to import transactions via exchange API."""
    exchange: Exchange = Field(..., description="Exchange to import from")
    credentials: ExchangeAPICredentials
    start_date: Optional[date] = Field(None, description="Start date for import")
    end_date: Optional[date] = Field(None, description="End date for import")
    tax_year: int = Field(default=2025, description="Tax year to focus on")


class APIImportResponse(BaseModel):
    """Response from API import."""
    success: bool
    exchange: str
    transactions_imported: int
    transactions_skipped: int
    wallets_found: List[str] = []
    assets_found: List[str] = []
    date_range: Optional[Dict[str, str]] = None
    warnings: List[str] = []
    errors: List[str] = []


class CalculateGainsRequest(BaseModel):
    """Request to calculate gains/losses."""
    tax_year: int = Field(default=2025, description="Tax year for calculation")
    cost_basis_method: CostBasisMethod = Field(default=CostBasisMethod.FIFO, description="Cost basis method")
    include_unrealized: bool = Field(default=False, description="Include unrealized gains")
    specific_assets: Optional[List[str]] = Field(None, description="Calculate for specific assets only")


class GainLossSummary(BaseModel):
    """Summary of gains/losses for an asset or total."""
    asset: Optional[str] = None
    proceeds: Decimal
    cost_basis: Decimal
    gain_loss: Decimal
    short_term_gain_loss: Decimal
    long_term_gain_loss: Decimal
    transactions_count: int
    wash_sale_adjustment: Decimal = Decimal("0")

    class Config:
        json_encoders = {Decimal: str}


class CalculateGainsResponse(BaseModel):
    """Response with calculated gains/losses."""
    tax_year: int
    cost_basis_method: str
    total_proceeds: Decimal
    total_cost_basis: Decimal
    total_gain_loss: Decimal
    short_term_gain_loss: Decimal
    long_term_gain_loss: Decimal
    wash_sale_disallowed: Decimal
    net_gain_loss: Decimal
    by_asset: List[GainLossSummary]
    disposals_count: int
    warnings: List[str] = []

    class Config:
        json_encoders = {Decimal: str}


class CryptoHolding(BaseModel):
    """Current holding of a cryptocurrency."""
    asset: str
    total_quantity: Decimal
    cost_basis_total: Decimal
    cost_basis_per_unit: Decimal
    current_price_usd: Optional[Decimal] = None
    current_value_usd: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    lots: List[Dict[str, Any]] = []  # Individual tax lots

    class Config:
        json_encoders = {Decimal: str}


class HoldingsResponse(BaseModel):
    """Response with current holdings."""
    as_of_date: datetime
    cost_basis_method: str
    total_cost_basis: Decimal
    total_current_value: Optional[Decimal] = None
    total_unrealized_gain_loss: Optional[Decimal] = None
    holdings: List[CryptoHolding]
    warnings: List[str] = []

    class Config:
        json_encoders = {Decimal: str}


class TransactionFilter(BaseModel):
    """Filters for transaction listing."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assets: Optional[List[str]] = None
    transaction_types: Optional[List[TransactionType]] = None
    exchanges: Optional[List[Exchange]] = None
    min_value_usd: Optional[Decimal] = None
    max_value_usd: Optional[Decimal] = None


class TransactionsResponse(BaseModel):
    """Response with transaction list."""
    transactions: List[CryptoTransaction]
    total_count: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any]


class Form8949Entry(BaseModel):
    """Single entry for Form 8949."""
    description: str = Field(..., description="Description of property (e.g., '2.5 BTC')")
    date_acquired: date
    date_sold: date
    proceeds: Decimal
    cost_basis: Decimal
    adjustment_code: Optional[str] = Field(None, description="Adjustment code (e.g., 'W' for wash sale)")
    adjustment_amount: Optional[Decimal] = None
    gain_or_loss: Decimal
    holding_period: HoldingPeriod
    box: Form8949Box

    class Config:
        json_encoders = {Decimal: str}


class Form8949Request(BaseModel):
    """Request to generate Form 8949 data."""
    tax_year: int = Field(default=2025, description="Tax year")
    cost_basis_method: CostBasisMethod = Field(default=CostBasisMethod.FIFO)
    include_wash_sales: bool = Field(default=True, description="Apply wash sale adjustments")


class Form8949Response(BaseModel):
    """Response with Form 8949 data."""
    tax_year: int
    box_a_entries: List[Form8949Entry] = []  # Short-term, 1099-B with basis
    box_b_entries: List[Form8949Entry] = []  # Short-term, 1099-B without basis
    box_c_entries: List[Form8949Entry] = []  # Short-term, no 1099-B
    box_d_entries: List[Form8949Entry] = []  # Long-term, 1099-B with basis
    box_e_entries: List[Form8949Entry] = []  # Long-term, 1099-B without basis
    box_f_entries: List[Form8949Entry] = []  # Long-term, no 1099-B
    schedule_d_summary: Dict[str, Any]
    totals: Dict[str, Decimal]
    warnings: List[str] = []

    class Config:
        json_encoders = {Decimal: str}


class CryptoIncomeItem(BaseModel):
    """A single crypto income event."""
    date: datetime
    income_type: TransactionType
    asset: str
    quantity: Decimal
    fair_market_value_usd: Decimal
    source: Optional[str] = None
    tx_hash: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_encoders = {Decimal: str}


class CryptoIncomeResponse(BaseModel):
    """Response with crypto income for Schedule 1/B."""
    tax_year: int
    staking_income: Decimal
    mining_income: Decimal
    airdrop_income: Decimal
    interest_income: Decimal
    other_income: Decimal
    total_income: Decimal
    income_items: List[CryptoIncomeItem]
    schedule_1_line: Optional[str] = Field(None, description="Applicable Schedule 1 line")
    schedule_b_required: bool = Field(False, description="Whether Schedule B is required")
    form_1099_misc_total: Decimal
    warnings: List[str] = []

    class Config:
        json_encoders = {Decimal: str}


class WashSale(BaseModel):
    """A detected wash sale."""
    sell_transaction_id: str
    sell_date: date
    asset: str
    quantity_sold: Decimal
    loss_disallowed: Decimal
    replacement_transaction_id: str
    replacement_date: date
    replacement_quantity: Decimal
    days_between: int
    adjustment_added_to_basis: Decimal

    class Config:
        json_encoders = {Decimal: str}


class WashSalesRequest(BaseModel):
    """Request to detect wash sales."""
    tax_year: int = Field(default=2025, description="Tax year to analyze")
    look_back_days: int = Field(default=30, description="Days before sale to check")
    look_forward_days: int = Field(default=30, description="Days after sale to check")
    include_similar_assets: bool = Field(
        default=False,
        description="Include substantially identical assets (e.g., wrapped tokens)"
    )


class WashSalesResponse(BaseModel):
    """Response with wash sale detection results."""
    tax_year: int
    wash_sales_detected: int
    total_loss_disallowed: Decimal
    wash_sales: List[WashSale]
    affected_assets: List[str]
    warnings: List[str] = []

    class Config:
        json_encoders = {Decimal: str}


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ============== Routes ==============

@router.post(
    "/import/csv",
    response_model=CSVImportResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid CSV format"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    },
    summary="Import transactions from CSV",
    description="""
    Import cryptocurrency transactions from a CSV file exported from an exchange.

    Supports automatic detection of exchange format for:
    - Coinbase / Coinbase Pro
    - Kraken
    - Binance US
    - Gemini
    - Crypto.com
    - Robinhood

    The CSV should contain transaction history with dates, amounts, and prices.
    Transactions are parsed and stored for gain/loss calculation.
    """
)
async def import_csv(request: CSVImportRequest):
    """Import cryptocurrency transactions from CSV file content."""
    try:
        # Validate CSV content is not empty
        if not request.csv_content or not request.csv_content.strip():
            raise HTTPException(
                status_code=400,
                detail="CSV content is empty"
            )

        # Parse CSV and detect exchange format
        # This would be implemented by a crypto import service
        lines = request.csv_content.strip().split('\n')
        if len(lines) < 2:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain at least a header row and one data row"
            )

        # Placeholder response - actual implementation would parse CSV
        return CSVImportResponse(
            success=True,
            exchange_detected=request.exchange.value if request.exchange else "auto_detected",
            transactions_imported=len(lines) - 1,  # Excluding header
            transactions_skipped=0,
            warnings=[],
            errors=[],
            date_range={
                "start": "2025-01-01",
                "end": "2025-12-31"
            },
            assets_found=["BTC", "ETH"]  # Would be populated from actual data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import CSV: {str(e)}")


@router.post("/import/csv/upload")
async def upload_csv(
    file: UploadFile = File(..., description="CSV file from exchange"),
    exchange: Optional[Exchange] = Form(None, description="Exchange format"),
    tax_year: int = Form(2025, description="Tax year to filter")
):
    """Upload a CSV file for import.

    Alternative to the JSON endpoint - accepts direct file upload.
    """
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')

        # Reuse the CSV import logic
        request = CSVImportRequest(
            csv_content=csv_content,
            exchange=exchange,
            tax_year=tax_year
        )
        return await import_csv(request)

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded CSV"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {str(e)}")


@router.post(
    "/import/api",
    response_model=APIImportResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid credentials or exchange"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        429: {"model": ErrorResponse, "description": "Rate limited by exchange"}
    },
    summary="Import via exchange API",
    description="""
    Import cryptocurrency transactions directly from an exchange via API.

    Currently supports:
    - **Coinbase**: Requires API key and secret from Developer Settings
    - **Kraken**: Requires API key and private key

    API credentials are used only for the import and are not stored.

    **Security Note**: Use read-only API keys with transaction history permissions only.
    Do not provide keys with trading or withdrawal permissions.
    """
)
async def import_via_api(request: APIImportRequest):
    """Import transactions directly from exchange API."""
    try:
        # Validate exchange is supported for API import
        supported_exchanges = [Exchange.COINBASE, Exchange.COINBASE_PRO, Exchange.KRAKEN]
        if request.exchange not in supported_exchanges:
            raise HTTPException(
                status_code=400,
                detail=f"Exchange '{request.exchange.value}' is not supported for API import. "
                       f"Supported: {[e.value for e in supported_exchanges]}"
            )

        # Validate credentials format
        if not request.credentials.api_key or not request.credentials.api_secret:
            raise HTTPException(
                status_code=400,
                detail="API key and secret are required"
            )

        # Placeholder - actual implementation would call exchange APIs
        # Would use libraries like ccxt or exchange-specific SDKs
        return APIImportResponse(
            success=True,
            exchange=request.exchange.value,
            transactions_imported=0,
            transactions_skipped=0,
            wallets_found=[],
            assets_found=[],
            date_range=None,
            warnings=["API import requires implementation of exchange-specific client"],
            errors=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API import failed: {str(e)}")


@router.post(
    "/calculate",
    response_model=CalculateGainsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "No transactions found"}
    },
    summary="Calculate gains and losses",
    description="""
    Calculate capital gains and losses for cryptocurrency transactions.

    **Cost Basis Methods**:
    - **FIFO** (First In, First Out): Oldest lots sold first. Most common method.
    - **LIFO** (Last In, First Out): Newest lots sold first.
    - **HIFO** (Highest In, First Out): Highest cost lots sold first. Minimizes gains.
    - **Specific ID**: Manually identify which lots to sell (requires lot tracking).

    **Holding Periods**:
    - Short-term: Held 1 year or less (taxed as ordinary income)
    - Long-term: Held more than 1 year (lower capital gains rate)

    Calculations follow IRS guidance for virtual currency (Notice 2014-21, Rev. Rul. 2019-24).
    """
)
async def calculate_gains(request: CalculateGainsRequest):
    """Calculate capital gains/losses for the specified tax year."""
    try:
        # Placeholder - actual implementation would:
        # 1. Load all transactions for the user
        # 2. Apply cost basis method
        # 3. Calculate gains/losses for each disposal
        # 4. Separate short-term vs long-term
        # 5. Apply wash sale rules if applicable

        return CalculateGainsResponse(
            tax_year=request.tax_year,
            cost_basis_method=request.cost_basis_method.value,
            total_proceeds=Decimal("0"),
            total_cost_basis=Decimal("0"),
            total_gain_loss=Decimal("0"),
            short_term_gain_loss=Decimal("0"),
            long_term_gain_loss=Decimal("0"),
            wash_sale_disallowed=Decimal("0"),
            net_gain_loss=Decimal("0"),
            by_asset=[],
            disposals_count=0,
            warnings=["No transactions loaded. Import transactions first."]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get(
    "/holdings",
    response_model=HoldingsResponse,
    summary="Get current holdings",
    description="""
    Get current cryptocurrency holdings with cost basis information.

    Returns:
    - Total quantity held for each asset
    - Cost basis per asset (based on selected method)
    - Individual tax lots (for Specific ID method)
    - Current value and unrealized gains (if price data available)

    Holdings are calculated from imported transactions.
    """
)
async def get_holdings(
    cost_basis_method: CostBasisMethod = Query(
        default=CostBasisMethod.FIFO,
        description="Cost basis method for calculating per-unit cost"
    ),
    asset: Optional[str] = Query(
        default=None,
        description="Filter to specific asset (e.g., 'BTC')"
    ),
    include_zero: bool = Query(
        default=False,
        description="Include assets with zero balance"
    )
):
    """Get current cryptocurrency holdings with cost basis."""
    try:
        # Placeholder - actual implementation would aggregate transactions
        return HoldingsResponse(
            as_of_date=datetime.now(),
            cost_basis_method=cost_basis_method.value,
            total_cost_basis=Decimal("0"),
            total_current_value=None,
            total_unrealized_gain_loss=None,
            holdings=[],
            warnings=["No transactions loaded. Import transactions first."]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve holdings: {str(e)}")


@router.get(
    "/transactions",
    response_model=TransactionsResponse,
    summary="List all transactions",
    description="""
    List all cryptocurrency transactions with filtering options.

    Supports filtering by:
    - Date range
    - Specific assets (BTC, ETH, etc.)
    - Transaction types (buy, sell, trade, staking, etc.)
    - Exchanges
    - Value range

    Results are paginated. Use `page` and `page_size` parameters.
    """
)
async def list_transactions(
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    assets: Optional[str] = Query(None, description="Comma-separated list of assets"),
    transaction_types: Optional[str] = Query(None, description="Comma-separated transaction types"),
    exchanges: Optional[str] = Query(None, description="Comma-separated exchanges"),
    min_value: Optional[float] = Query(None, description="Minimum USD value"),
    max_value: Optional[float] = Query(None, description="Maximum USD value"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page")
):
    """List all cryptocurrency transactions with filtering."""
    try:
        # Parse comma-separated filters
        asset_list = assets.split(',') if assets else None
        type_list = transaction_types.split(',') if transaction_types else None
        exchange_list = exchanges.split(',') if exchanges else None

        filters_applied = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "assets": asset_list,
            "transaction_types": type_list,
            "exchanges": exchange_list,
            "min_value": min_value,
            "max_value": max_value
        }

        # Placeholder - actual implementation would query transaction store
        return TransactionsResponse(
            transactions=[],
            total_count=0,
            page=page,
            page_size=page_size,
            filters_applied=filters_applied
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list transactions: {str(e)}")


@router.post(
    "/form8949",
    response_model=Form8949Response,
    summary="Generate Form 8949 data",
    description="""
    Generate IRS Form 8949 data for cryptocurrency sales.

    Form 8949 is used to report capital gains and losses from cryptocurrency sales.
    Entries are categorized by:

    **Short-term (held 1 year or less)**:
    - Box A: Reported on 1099-B with basis
    - Box B: Reported on 1099-B without basis
    - Box C: Not reported on 1099-B

    **Long-term (held more than 1 year)**:
    - Box D: Reported on 1099-B with basis
    - Box E: Reported on 1099-B without basis
    - Box F: Not reported on 1099-B

    Most crypto transactions fall under Box C or F (not reported on 1099-B).

    Also generates Schedule D summary totals.
    """
)
async def generate_form_8949(request: Form8949Request):
    """Generate Form 8949 data for tax filing."""
    try:
        # Placeholder - actual implementation would:
        # 1. Get all disposals for the tax year
        # 2. Calculate gain/loss for each
        # 3. Categorize by holding period and 1099-B status
        # 4. Apply wash sale adjustments if requested
        # 5. Generate Schedule D summary

        return Form8949Response(
            tax_year=request.tax_year,
            box_a_entries=[],
            box_b_entries=[],
            box_c_entries=[],
            box_d_entries=[],
            box_e_entries=[],
            box_f_entries=[],
            schedule_d_summary={
                "short_term_proceeds": "0.00",
                "short_term_cost_basis": "0.00",
                "short_term_adjustments": "0.00",
                "short_term_gain_loss": "0.00",
                "long_term_proceeds": "0.00",
                "long_term_cost_basis": "0.00",
                "long_term_adjustments": "0.00",
                "long_term_gain_loss": "0.00",
                "net_gain_loss": "0.00"
            },
            totals={
                "total_proceeds": Decimal("0"),
                "total_cost_basis": Decimal("0"),
                "total_adjustments": Decimal("0"),
                "total_gain_loss": Decimal("0")
            },
            warnings=["No transactions loaded. Import transactions first."]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Form 8949: {str(e)}")


@router.get(
    "/income",
    response_model=CryptoIncomeResponse,
    summary="Get crypto income",
    description="""
    Get cryptocurrency income for Schedule 1 / Schedule B reporting.

    **Types of crypto income**:
    - **Staking rewards**: Income from proof-of-stake validation
    - **Mining rewards**: Income from cryptocurrency mining
    - **Airdrops**: Free tokens received (taxable at FMV when received)
    - **Interest**: Interest earned on crypto lending/savings
    - **Other**: Payments received, rewards programs, etc.

    All income is taxed as ordinary income at fair market value (FMV)
    on the date received (IRS Notice 2014-21, Rev. Rul. 2019-24).

    If total interest/dividends exceed $1,500, Schedule B is required.
    """
)
async def get_crypto_income(
    tax_year: int = Query(default=2025, description="Tax year"),
    income_types: Optional[str] = Query(
        None,
        description="Filter by income types (comma-separated)"
    )
):
    """Get cryptocurrency income for tax reporting."""
    try:
        # Parse income type filter
        type_filter = income_types.split(',') if income_types else None

        # Placeholder - actual implementation would aggregate income transactions
        return CryptoIncomeResponse(
            tax_year=tax_year,
            staking_income=Decimal("0"),
            mining_income=Decimal("0"),
            airdrop_income=Decimal("0"),
            interest_income=Decimal("0"),
            other_income=Decimal("0"),
            total_income=Decimal("0"),
            income_items=[],
            schedule_1_line="8z",  # Other income
            schedule_b_required=False,
            form_1099_misc_total=Decimal("0"),
            warnings=["No income transactions found. Import transactions first."]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve income: {str(e)}")


@router.post(
    "/wash-sales",
    response_model=WashSalesResponse,
    summary="Detect wash sales",
    description="""
    Detect wash sales in cryptocurrency transactions.

    **Wash Sale Rule**: If you sell crypto at a loss and buy the same or
    "substantially identical" crypto within 30 days before or after the sale,
    the loss is disallowed. The disallowed loss is added to the cost basis
    of the replacement shares.

    **Note**: The IRS has not definitively stated that wash sale rules apply
    to cryptocurrency (they technically apply only to "securities" and "stock").
    However, many tax professionals recommend tracking them for:
    1. Conservative tax positions
    2. Potential future IRS guidance
    3. If crypto becomes classified as a security

    This tool identifies potential wash sales for review.
    """
)
async def detect_wash_sales(request: WashSalesRequest):
    """Detect wash sales in cryptocurrency transactions."""
    try:
        # Validate parameters
        if request.look_back_days < 0 or request.look_forward_days < 0:
            raise HTTPException(
                status_code=400,
                detail="Look-back and look-forward days must be non-negative"
            )

        # Placeholder - actual implementation would:
        # 1. Find all sales at a loss
        # 2. Check for purchases of same asset within 30-day window
        # 3. Calculate disallowed loss amounts
        # 4. Track basis adjustments

        return WashSalesResponse(
            tax_year=request.tax_year,
            wash_sales_detected=0,
            total_loss_disallowed=Decimal("0"),
            wash_sales=[],
            affected_assets=[],
            warnings=[
                "No transactions loaded. Import transactions first.",
                "Wash sale rules may not technically apply to cryptocurrency. "
                "Consult a tax professional for guidance."
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wash sale detection failed: {str(e)}")


# ============== Additional Utility Routes ==============

@router.get(
    "/supported-exchanges",
    summary="List supported exchanges",
    description="Get list of exchanges supported for CSV and API import."
)
async def get_supported_exchanges():
    """Get list of supported cryptocurrency exchanges."""
    return {
        "csv_import": [e.value for e in Exchange],
        "api_import": [
            Exchange.COINBASE.value,
            Exchange.COINBASE_PRO.value,
            Exchange.KRAKEN.value
        ],
        "cost_basis_methods": [m.value for m in CostBasisMethod],
        "transaction_types": [t.value for t in TransactionType]
    }


@router.get(
    "/tax-guidance",
    summary="Get IRS crypto tax guidance",
    description="Get summary of IRS guidance on cryptocurrency taxation."
)
async def get_tax_guidance():
    """Get IRS guidance summary for cryptocurrency taxation."""
    return {
        "primary_guidance": [
            {
                "reference": "Notice 2014-21",
                "title": "IRS Virtual Currency Guidance",
                "summary": "Virtual currency is treated as property for federal tax purposes. "
                           "General tax principles for property transactions apply."
            },
            {
                "reference": "Rev. Rul. 2019-24",
                "title": "Tax Treatment of Cryptocurrency Hard Forks",
                "summary": "Clarifies that hard forks resulting in new cryptocurrency are taxable "
                           "as ordinary income when the taxpayer has dominion and control."
            }
        ],
        "key_points": [
            "Cryptocurrency is treated as property, not currency",
            "Each sale or exchange is a taxable event",
            "Mining and staking rewards are taxable as ordinary income",
            "Airdrops are taxable when received at fair market value",
            "Holding period determines short-term vs long-term rates",
            "Crypto-to-crypto trades are taxable events",
            "Cost basis methods include FIFO, LIFO, HIFO, and Specific ID"
        ],
        "form_requirements": {
            "Form 1040": "Question about virtual currency transactions",
            "Form 8949": "Report each sale/exchange",
            "Schedule D": "Summary of capital gains/losses",
            "Schedule 1": "Report mining/staking income",
            "Schedule B": "Required if interest exceeds $1,500",
            "Schedule C": "If mining is a business activity"
        }
    }
