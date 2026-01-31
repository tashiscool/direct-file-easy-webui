"""Brokerage CSV Import Service for Form 8949 and Schedule D.

Supports import from major brokerages:
- TD Ameritrade / Charles Schwab
- Fidelity
- Vanguard
- Robinhood
- E*Trade
- Interactive Brokers
"""

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class BrokerageType(str, Enum):
    """Supported brokerage formats."""
    TD_AMERITRADE = "TD Ameritrade"
    SCHWAB = "Charles Schwab"
    FIDELITY = "Fidelity"
    VANGUARD = "Vanguard"
    ROBINHOOD = "Robinhood"
    ETRADE = "E*Trade"
    INTERACTIVE_BROKERS = "Interactive Brokers"
    GENERIC = "Generic CSV"
    UNKNOWN = "Unknown"


class TransactionType(str, Enum):
    """Type of securities transaction."""
    STOCK_SALE = "Stock Sale"
    OPTION_SALE = "Option Sale"
    MUTUAL_FUND_SALE = "Mutual Fund Sale"
    ETF_SALE = "ETF Sale"
    BOND_SALE = "Bond Sale"
    CRYPTO_SALE = "Cryptocurrency Sale"
    SHORT_SALE = "Short Sale"
    WASH_SALE = "Wash Sale"


class HoldingPeriod(str, Enum):
    """Holding period for capital gains classification."""
    SHORT_TERM = "Short-term"  # Held 1 year or less
    LONG_TERM = "Long-term"    # Held more than 1 year
    UNKNOWN = "Unknown"


class CostBasisReporting(str, Enum):
    """IRS cost basis reporting category."""
    CATEGORY_A = "A"  # Short-term, basis reported to IRS
    CATEGORY_B = "B"  # Short-term, basis NOT reported to IRS
    CATEGORY_C = "C"  # Short-term, form 1099-B not received
    CATEGORY_D = "D"  # Long-term, basis reported to IRS
    CATEGORY_E = "E"  # Long-term, basis NOT reported to IRS
    CATEGORY_F = "F"  # Long-term, form 1099-B not received


@dataclass
class SecurityTransaction:
    """A single securities transaction for Form 8949."""
    symbol: str
    description: str
    quantity: Decimal
    date_acquired: Optional[datetime]
    date_sold: datetime
    proceeds: Decimal
    cost_basis: Decimal
    adjustment_amount: Decimal = Decimal("0")
    adjustment_code: str = ""
    gain_or_loss: Decimal = Decimal("0")
    holding_period: HoldingPeriod = HoldingPeriod.UNKNOWN
    cost_basis_reporting: CostBasisReporting = CostBasisReporting.CATEGORY_A
    transaction_type: TransactionType = TransactionType.STOCK_SALE
    is_wash_sale: bool = False
    wash_sale_loss_disallowed: Decimal = Decimal("0")
    accrued_market_discount: Decimal = Decimal("0")
    cusip: Optional[str] = None
    form_8949_line: int = 0  # Line number on Form 8949

    def __post_init__(self):
        """Calculate gain/loss and determine holding period."""
        self.gain_or_loss = self.proceeds - self.cost_basis - self.adjustment_amount

        if self.date_acquired and self.date_sold:
            days_held = (self.date_sold - self.date_acquired).days
            self.holding_period = (
                HoldingPeriod.LONG_TERM if days_held > 365
                else HoldingPeriod.SHORT_TERM
            )


@dataclass
class BrokerageImportResult:
    """Result of importing brokerage data."""
    brokerage_type: BrokerageType
    transactions: List[SecurityTransaction] = field(default_factory=list)
    total_proceeds: Decimal = Decimal("0")
    total_cost_basis: Decimal = Decimal("0")
    total_gain_or_loss: Decimal = Decimal("0")
    short_term_gain_or_loss: Decimal = Decimal("0")
    long_term_gain_or_loss: Decimal = Decimal("0")
    wash_sale_adjustments: Decimal = Decimal("0")
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    form_8949_data: Dict[str, Any] = field(default_factory=dict)
    schedule_d_data: Dict[str, Any] = field(default_factory=dict)


class BrokerageCSVImporter:
    """Imports and processes brokerage CSV files for tax reporting."""

    # Column mappings for different brokerages
    COLUMN_MAPPINGS = {
        BrokerageType.TD_AMERITRADE: {
            "symbol": ["Symbol", "SYMBOL"],
            "description": ["Description", "DESCRIPTION", "Security Name"],
            "quantity": ["Qty", "Quantity", "QTY", "Shares"],
            "date_acquired": ["Date Acquired", "Acquired Date", "Purchase Date"],
            "date_sold": ["Date Sold", "Sold Date", "Sale Date"],
            "proceeds": ["Proceeds", "PROCEEDS", "Sale Proceeds", "Gross Proceeds"],
            "cost_basis": ["Cost Basis", "Cost", "Cost or Other Basis"],
            "gain_loss": ["Gain/Loss", "Gain or Loss", "Realized Gain/Loss"],
            "wash_sale": ["Wash Sale Loss Disallowed", "Wash Sale Adj"],
        },
        BrokerageType.SCHWAB: {
            "symbol": ["Symbol", "SYMBOL"],
            "description": ["Description", "Security Description"],
            "quantity": ["Quantity", "Shares Sold"],
            "date_acquired": ["Date Acquired"],
            "date_sold": ["Date Sold", "Sale Date"],
            "proceeds": ["Proceeds", "Gross Proceeds"],
            "cost_basis": ["Cost Basis", "Reported Cost Basis"],
            "gain_loss": ["Short-term gain or loss", "Long-term gain or loss", "Gain(Loss)"],
            "term": ["Term", "Holding Period"],
        },
        BrokerageType.FIDELITY: {
            "symbol": ["Symbol"],
            "description": ["Security Description", "Description"],
            "quantity": ["Quantity"],
            "date_acquired": ["Date Acquired", "Acquired"],
            "date_sold": ["Date Sold", "Sold"],
            "proceeds": ["Proceeds"],
            "cost_basis": ["Cost Basis"],
            "gain_loss": ["Gain/Loss ($)", "Gain or (Loss)"],
            "term": ["Term"],
        },
        BrokerageType.VANGUARD: {
            "symbol": ["Investment", "Symbol"],
            "description": ["Investment Name", "Description"],
            "quantity": ["Shares", "Units"],
            "date_acquired": ["Date Acquired"],
            "date_sold": ["Date Sold"],
            "proceeds": ["Proceeds"],
            "cost_basis": ["Cost Basis"],
            "gain_loss": ["Gain/Loss", "Total Gain/Loss"],
        },
        BrokerageType.ROBINHOOD: {
            "symbol": ["Symbol", "Ticker"],
            "description": ["Description", "Name"],
            "quantity": ["Quantity", "Shares"],
            "date_acquired": ["Date Acquired", "Acquired Date"],
            "date_sold": ["Date Sold", "Sold Date"],
            "proceeds": ["Proceeds", "Total Proceeds"],
            "cost_basis": ["Cost Basis"],
            "gain_loss": ["Gain/Loss"],
        },
    }

    def __init__(self):
        """Initialize the importer."""
        pass

    def detect_brokerage_type(self, csv_content: str) -> BrokerageType:
        """Detect which brokerage format the CSV is from."""
        content_lower = csv_content.lower()

        # Check for brokerage-specific indicators
        if "td ameritrade" in content_lower or "tda" in content_lower:
            return BrokerageType.TD_AMERITRADE
        elif "schwab" in content_lower:
            return BrokerageType.SCHWAB
        elif "fidelity" in content_lower:
            return BrokerageType.FIDELITY
        elif "vanguard" in content_lower:
            return BrokerageType.VANGUARD
        elif "robinhood" in content_lower:
            return BrokerageType.ROBINHOOD
        elif "e*trade" in content_lower or "etrade" in content_lower:
            return BrokerageType.ETRADE
        elif "interactive brokers" in content_lower:
            return BrokerageType.INTERACTIVE_BROKERS

        return BrokerageType.GENERIC

    def import_csv(
        self,
        csv_content: str,
        brokerage_type: Optional[BrokerageType] = None,
        tax_year: int = 2025
    ) -> BrokerageImportResult:
        """Import a brokerage CSV file.

        Args:
            csv_content: The CSV file content as string.
            brokerage_type: Optional brokerage type override.
            tax_year: Tax year for filtering transactions.

        Returns:
            BrokerageImportResult with parsed transactions.
        """
        # Detect brokerage if not specified
        if not brokerage_type:
            brokerage_type = self.detect_brokerage_type(csv_content)

        result = BrokerageImportResult(brokerage_type=brokerage_type)

        try:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            column_mapping = self._get_column_mapping(brokerage_type, reader.fieldnames)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header row
                try:
                    transaction = self._parse_row(row, column_mapping, brokerage_type)
                    if transaction:
                        # Filter by tax year if date_sold is in the target year
                        if transaction.date_sold.year == tax_year:
                            result.transactions.append(transaction)
                except Exception as e:
                    result.warnings.append(f"Row {row_num}: {str(e)}")

        except Exception as e:
            result.errors.append(f"Failed to parse CSV: {str(e)}")
            return result

        # Calculate totals
        self._calculate_totals(result)

        # Generate Form 8949 and Schedule D data
        result.form_8949_data = self._generate_form_8949_data(result)
        result.schedule_d_data = self._generate_schedule_d_data(result)

        return result

    def import_file(
        self,
        file_path: Path,
        brokerage_type: Optional[BrokerageType] = None,
        tax_year: int = 2025
    ) -> BrokerageImportResult:
        """Import a brokerage CSV file from disk."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.import_csv(f.read(), brokerage_type, tax_year)

    def _get_column_mapping(
        self,
        brokerage_type: BrokerageType,
        csv_headers: List[str]
    ) -> Dict[str, str]:
        """Map CSV column names to our standard field names."""
        mapping = {}
        header_lower = {h.lower(): h for h in csv_headers}

        # Get brokerage-specific mappings
        brokerage_mappings = self.COLUMN_MAPPINGS.get(
            brokerage_type,
            self.COLUMN_MAPPINGS[BrokerageType.TD_AMERITRADE]  # Default
        )

        for field_name, possible_columns in brokerage_mappings.items():
            for col in possible_columns:
                col_lower = col.lower()
                if col_lower in header_lower:
                    mapping[field_name] = header_lower[col_lower]
                    break

        return mapping

    def _parse_row(
        self,
        row: Dict[str, str],
        column_mapping: Dict[str, str],
        brokerage_type: BrokerageType
    ) -> Optional[SecurityTransaction]:
        """Parse a single CSV row into a SecurityTransaction."""

        def get_value(field: str) -> Optional[str]:
            col = column_mapping.get(field)
            if col and col in row:
                val = row[col].strip()
                return val if val else None
            return None

        def parse_decimal(value: Optional[str]) -> Decimal:
            if not value:
                return Decimal("0")
            # Remove currency symbols, commas, parentheses (for negative)
            cleaned = re.sub(r'[$,()]', '', value)
            cleaned = cleaned.replace('(', '-').replace(')', '')
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                return Decimal("0")

        def parse_date(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            # Try common date formats
            formats = [
                "%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y",
                "%m/%d/%y", "%Y/%m/%d", "%d-%b-%Y",
                "%B %d, %Y", "%b %d, %Y"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            return None

        # Extract required fields
        symbol = get_value("symbol")
        date_sold_str = get_value("date_sold")

        if not symbol or not date_sold_str:
            return None

        date_sold = parse_date(date_sold_str)
        if not date_sold:
            return None

        # Build transaction
        return SecurityTransaction(
            symbol=symbol,
            description=get_value("description") or symbol,
            quantity=parse_decimal(get_value("quantity")),
            date_acquired=parse_date(get_value("date_acquired")),
            date_sold=date_sold,
            proceeds=parse_decimal(get_value("proceeds")),
            cost_basis=parse_decimal(get_value("cost_basis")),
            wash_sale_loss_disallowed=parse_decimal(get_value("wash_sale"))
        )

    def _calculate_totals(self, result: BrokerageImportResult) -> None:
        """Calculate summary totals from transactions."""
        for txn in result.transactions:
            result.total_proceeds += txn.proceeds
            result.total_cost_basis += txn.cost_basis
            result.total_gain_or_loss += txn.gain_or_loss

            if txn.holding_period == HoldingPeriod.SHORT_TERM:
                result.short_term_gain_or_loss += txn.gain_or_loss
            elif txn.holding_period == HoldingPeriod.LONG_TERM:
                result.long_term_gain_or_loss += txn.gain_or_loss

            result.wash_sale_adjustments += txn.wash_sale_loss_disallowed

    def _generate_form_8949_data(
        self,
        result: BrokerageImportResult
    ) -> Dict[str, Any]:
        """Generate Form 8949 data structure."""
        # Categorize transactions for Form 8949
        categories = {
            "partI_categoryA": [],  # Short-term, basis reported
            "partI_categoryB": [],  # Short-term, basis not reported
            "partI_categoryC": [],  # Short-term, no 1099-B
            "partII_categoryD": [], # Long-term, basis reported
            "partII_categoryE": [], # Long-term, basis not reported
            "partII_categoryF": [], # Long-term, no 1099-B
        }

        for txn in result.transactions:
            entry = {
                "description": f"{txn.quantity} sh {txn.symbol}",
                "dateAcquired": txn.date_acquired.strftime("%m/%d/%Y") if txn.date_acquired else "Various",
                "dateSold": txn.date_sold.strftime("%m/%d/%Y"),
                "proceeds": str(txn.proceeds),
                "costBasis": str(txn.cost_basis),
                "adjustmentCode": txn.adjustment_code or ("W" if txn.is_wash_sale else ""),
                "adjustmentAmount": str(txn.adjustment_amount),
                "gainOrLoss": str(txn.gain_or_loss)
            }

            # Categorize based on holding period and cost basis reporting
            if txn.holding_period == HoldingPeriod.SHORT_TERM:
                if txn.cost_basis_reporting == CostBasisReporting.CATEGORY_A:
                    categories["partI_categoryA"].append(entry)
                elif txn.cost_basis_reporting == CostBasisReporting.CATEGORY_B:
                    categories["partI_categoryB"].append(entry)
                else:
                    categories["partI_categoryC"].append(entry)
            else:  # Long-term
                if txn.cost_basis_reporting == CostBasisReporting.CATEGORY_D:
                    categories["partII_categoryD"].append(entry)
                elif txn.cost_basis_reporting == CostBasisReporting.CATEGORY_E:
                    categories["partII_categoryE"].append(entry)
                else:
                    categories["partII_categoryF"].append(entry)

        return {
            "form": "8949",
            "taxYear": 2025,
            "categories": categories,
            "totalShortTermProceeds": str(sum(
                Decimal(e["proceeds"]) for cat in ["partI_categoryA", "partI_categoryB", "partI_categoryC"]
                for e in categories[cat]
            )),
            "totalShortTermCostBasis": str(sum(
                Decimal(e["costBasis"]) for cat in ["partI_categoryA", "partI_categoryB", "partI_categoryC"]
                for e in categories[cat]
            )),
            "totalShortTermGainLoss": str(result.short_term_gain_or_loss),
            "totalLongTermProceeds": str(sum(
                Decimal(e["proceeds"]) for cat in ["partII_categoryD", "partII_categoryE", "partII_categoryF"]
                for e in categories[cat]
            )),
            "totalLongTermCostBasis": str(sum(
                Decimal(e["costBasis"]) for cat in ["partII_categoryD", "partII_categoryE", "partII_categoryF"]
                for e in categories[cat]
            )),
            "totalLongTermGainLoss": str(result.long_term_gain_or_loss),
        }

    def _generate_schedule_d_data(
        self,
        result: BrokerageImportResult
    ) -> Dict[str, Any]:
        """Generate Schedule D data structure."""
        return {
            "form": "Schedule D",
            "taxYear": 2025,
            # Part I - Short-Term Capital Gains and Losses
            "line1a": str(result.short_term_gain_or_loss),  # From Form 8949 Part I
            "line4": str(result.short_term_gain_or_loss),   # Short-term gain from Form 8949
            "line7": str(result.short_term_gain_or_loss),   # Net short-term capital gain or loss

            # Part II - Long-Term Capital Gains and Losses
            "line8a": str(result.long_term_gain_or_loss),   # From Form 8949 Part II
            "line11": str(result.long_term_gain_or_loss),   # Long-term gain from Form 8949
            "line15": str(result.long_term_gain_or_loss),   # Net long-term capital gain or loss

            # Summary
            "line16": str(result.total_gain_or_loss),       # Net capital gain or loss
            "washSaleAdjustments": str(result.wash_sale_adjustments),
        }


class CostBasisTracker:
    """Multi-year cost basis tracking for investments."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize cost basis tracker.

        Args:
            storage_path: Path to persist cost basis data.
        """
        self.storage_path = storage_path
        self.holdings: Dict[str, List[Dict]] = {}  # Symbol -> list of lots
        self._load_data()

    def _load_data(self):
        """Load persisted cost basis data."""
        if self.storage_path and self.storage_path.exists():
            import json
            with open(self.storage_path, 'r') as f:
                self.holdings = json.load(f)

    def _save_data(self):
        """Save cost basis data to disk."""
        if self.storage_path:
            import json
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.holdings, f, default=str, indent=2)

    def add_purchase(
        self,
        symbol: str,
        quantity: Decimal,
        price_per_share: Decimal,
        date: datetime,
        fees: Decimal = Decimal("0")
    ) -> None:
        """Record a purchase for cost basis tracking."""
        if symbol not in self.holdings:
            self.holdings[symbol] = []

        self.holdings[symbol].append({
            "quantity": str(quantity),
            "price_per_share": str(price_per_share),
            "total_cost": str(quantity * price_per_share + fees),
            "date_acquired": date.isoformat(),
            "remaining_quantity": str(quantity)
        })

        self._save_data()

    def calculate_cost_basis(
        self,
        symbol: str,
        quantity: Decimal,
        date_sold: datetime,
        method: str = "FIFO"
    ) -> Tuple[Decimal, List[Dict]]:
        """Calculate cost basis for a sale using specified method.

        Args:
            symbol: Stock symbol.
            quantity: Shares sold.
            date_sold: Sale date.
            method: Cost basis method (FIFO, LIFO, SpecificID, AverageCost).

        Returns:
            Tuple of (total_cost_basis, list_of_lots_used).
        """
        if symbol not in self.holdings:
            return Decimal("0"), []

        lots = self.holdings[symbol]
        if method == "FIFO":
            lots = sorted(lots, key=lambda x: x["date_acquired"])
        elif method == "LIFO":
            lots = sorted(lots, key=lambda x: x["date_acquired"], reverse=True)
        # AverageCost and SpecificID would need different handling

        remaining_to_sell = quantity
        total_basis = Decimal("0")
        lots_used = []

        for lot in lots:
            if remaining_to_sell <= 0:
                break

            available = Decimal(lot["remaining_quantity"])
            if available <= 0:
                continue

            shares_from_lot = min(available, remaining_to_sell)
            price_per_share = Decimal(lot["price_per_share"])
            lot_basis = shares_from_lot * price_per_share

            total_basis += lot_basis
            remaining_to_sell -= shares_from_lot

            # Update remaining quantity
            lot["remaining_quantity"] = str(available - shares_from_lot)

            lots_used.append({
                "date_acquired": lot["date_acquired"],
                "shares": str(shares_from_lot),
                "cost_basis": str(lot_basis),
                "price_per_share": str(price_per_share)
            })

        self._save_data()
        return total_basis, lots_used

    def get_holdings_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of current holdings and unrealized gains."""
        summary = {}

        symbols = [symbol] if symbol else list(self.holdings.keys())

        for sym in symbols:
            if sym not in self.holdings:
                continue

            lots = self.holdings[sym]
            total_shares = sum(Decimal(lot["remaining_quantity"]) for lot in lots)
            total_cost = sum(
                Decimal(lot["remaining_quantity"]) * Decimal(lot["price_per_share"])
                for lot in lots
            )

            summary[sym] = {
                "total_shares": str(total_shares),
                "total_cost_basis": str(total_cost),
                "average_cost_per_share": str(total_cost / total_shares) if total_shares > 0 else "0",
                "lots_count": len([l for l in lots if Decimal(l["remaining_quantity"]) > 0])
            }

        return summary
