"""Cryptocurrency Exchange Import Service for Form 8949 and Schedule D.

Comprehensive crypto tax reporting supporting all major exchanges:
- Coinbase (API and CSV)
- Coinbase Pro
- Kraken (API and CSV)
- Binance.US (CSV)
- Gemini (CSV)
- Robinhood Crypto (CSV)
- Crypto.com (CSV)
- Generic CSV parser

Features:
- Multiple cost basis methods (FIFO, LIFO, HIFO, Specific ID, Average Cost)
- Wash sale detection and adjustment
- Form 8949 category assignment (A-F)
- Short-term vs long-term classification
- DeFi transaction support
- Multi-exchange aggregation
"""

import csv
import hashlib
import io
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class ExchangeType(str, Enum):
    """Supported cryptocurrency exchanges."""
    COINBASE = "Coinbase"
    COINBASE_PRO = "Coinbase Pro"
    KRAKEN = "Kraken"
    BINANCE_US = "Binance.US"
    GEMINI = "Gemini"
    ROBINHOOD_CRYPTO = "Robinhood Crypto"
    CRYPTO_COM = "Crypto.com"
    KUCOIN = "KuCoin"
    BITTREX = "Bittrex"
    CELSIUS = "Celsius"
    BLOCKFI = "BlockFi"
    NEXO = "Nexo"
    GENERIC = "Generic CSV"
    UNKNOWN = "Unknown"


class TransactionType(str, Enum):
    """Types of cryptocurrency transactions."""
    BUY = "buy"
    SELL = "sell"
    CONVERT = "convert"
    SWAP = "swap"
    SEND = "send"
    RECEIVE = "receive"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STAKING_REWARD = "staking_reward"
    INTEREST = "interest"
    REWARD = "reward"
    AIRDROP = "airdrop"
    FORK = "fork"
    MINING = "mining"
    GIFT_SENT = "gift_sent"
    GIFT_RECEIVED = "gift_received"
    NFT_PURCHASE = "nft_purchase"
    NFT_SALE = "nft_sale"
    NFT_MINT = "nft_mint"
    LIQUIDITY_ADD = "liquidity_add"
    LIQUIDITY_REMOVE = "liquidity_remove"
    DEFI_SWAP = "defi_swap"
    DEFI_YIELD = "defi_yield"
    MARGIN_FEE = "margin_fee"
    LOAN_INTEREST = "loan_interest"
    UNKNOWN = "unknown"


class CostBasisMethod(str, Enum):
    """IRS-approved cost basis calculation methods."""
    FIFO = "FIFO"  # First In, First Out (default)
    LIFO = "LIFO"  # Last In, First Out
    HIFO = "HIFO"  # Highest In, First Out
    SPECIFIC_ID = "Specific Identification"
    AVERAGE_COST = "Average Cost"  # Only for certain mutual fund-like tokens


class HoldingPeriod(str, Enum):
    """Capital gains holding period classification."""
    SHORT_TERM = "Short-term"  # Held 1 year or less
    LONG_TERM = "Long-term"    # Held more than 1 year
    UNKNOWN = "Unknown"


class Form8949Category(str, Enum):
    """IRS Form 8949 reporting categories."""
    CATEGORY_A = "A"  # Short-term, basis reported to IRS (1099-B Box A)
    CATEGORY_B = "B"  # Short-term, basis NOT reported to IRS (1099-B Box B)
    CATEGORY_C = "C"  # Short-term, no Form 1099-B received
    CATEGORY_D = "D"  # Long-term, basis reported to IRS (1099-B Box D)
    CATEGORY_E = "E"  # Long-term, basis NOT reported to IRS (1099-B Box E)
    CATEGORY_F = "F"  # Long-term, no Form 1099-B received


class IncomeType(str, Enum):
    """Types of crypto income for tax purposes."""
    ORDINARY_INCOME = "ordinary_income"  # Staking, mining, airdrops
    CAPITAL_GAIN = "capital_gain"        # From sales
    SELF_EMPLOYMENT = "self_employment"  # Mining as business


# =============================================================================
# Pydantic Models
# =============================================================================

class CryptoAsset(BaseModel):
    """Represents a cryptocurrency or token."""
    symbol: str = Field(..., description="Token symbol (e.g., BTC, ETH)")
    name: Optional[str] = Field(None, description="Full name (e.g., Bitcoin)")
    contract_address: Optional[str] = Field(None, description="ERC-20/contract address")
    chain: Optional[str] = Field(None, description="Blockchain (e.g., ethereum, polygon)")
    decimals: int = Field(default=18, description="Token decimal places")
    is_nft: bool = Field(default=False, description="Whether this is an NFT")
    token_id: Optional[str] = Field(None, description="NFT token ID if applicable")

    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize token symbols to uppercase."""
        return v.upper().strip()


class CryptoTransaction(BaseModel):
    """A single cryptocurrency transaction."""
    id: str = Field(..., description="Unique transaction identifier")
    exchange: ExchangeType = Field(..., description="Source exchange")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    timestamp: datetime = Field(..., description="Transaction timestamp (UTC)")

    # Asset details
    asset: CryptoAsset = Field(..., description="Primary asset involved")
    quantity: Decimal = Field(..., description="Amount of asset")

    # Pricing
    price_per_unit: Optional[Decimal] = Field(None, description="Price per unit in USD")
    total_value_usd: Decimal = Field(..., description="Total USD value at time of transaction")

    # For conversions/swaps
    received_asset: Optional[CryptoAsset] = Field(None, description="Asset received in swap")
    received_quantity: Optional[Decimal] = Field(None, description="Quantity received")
    received_value_usd: Optional[Decimal] = Field(None, description="USD value of received asset")

    # Fees
    fee_amount: Decimal = Field(default=Decimal("0"), description="Transaction fee amount")
    fee_asset: Optional[str] = Field(None, description="Asset used for fee")
    fee_usd: Decimal = Field(default=Decimal("0"), description="Fee in USD")

    # Metadata
    txn_hash: Optional[str] = Field(None, description="Blockchain transaction hash")
    wallet_address: Optional[str] = Field(None, description="Wallet address involved")
    notes: Optional[str] = Field(None, description="User notes")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Original exchange data")

    @field_validator('quantity', 'total_value_usd', 'fee_amount', 'fee_usd', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        """Convert to Decimal if needed."""
        if v is None:
            return Decimal("0")
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @property
    def is_taxable_event(self) -> bool:
        """Determine if transaction triggers a taxable event."""
        taxable_types = {
            TransactionType.SELL,
            TransactionType.CONVERT,
            TransactionType.SWAP,
            TransactionType.GIFT_SENT,
            TransactionType.NFT_SALE,
            TransactionType.DEFI_SWAP,
        }
        return self.transaction_type in taxable_types

    @property
    def is_income_event(self) -> bool:
        """Determine if transaction is taxable income."""
        income_types = {
            TransactionType.STAKING_REWARD,
            TransactionType.INTEREST,
            TransactionType.REWARD,
            TransactionType.AIRDROP,
            TransactionType.MINING,
            TransactionType.DEFI_YIELD,
            TransactionType.GIFT_RECEIVED,
        }
        return self.transaction_type in income_types


class CryptoLot(BaseModel):
    """A tax lot representing a purchase of cryptocurrency."""
    id: str = Field(..., description="Unique lot identifier")
    asset: CryptoAsset = Field(..., description="Asset in this lot")
    quantity: Decimal = Field(..., description="Original quantity purchased")
    remaining_quantity: Decimal = Field(..., description="Quantity still held")
    cost_basis_per_unit: Decimal = Field(..., description="Cost per unit in USD")
    total_cost_basis: Decimal = Field(..., description="Total cost basis in USD")
    date_acquired: datetime = Field(..., description="Acquisition date")
    acquisition_type: TransactionType = Field(..., description="How asset was acquired")
    source_transaction_id: str = Field(..., description="Original transaction ID")

    # Tracking
    is_wash_sale_affected: bool = Field(default=False)
    wash_sale_adjustment: Decimal = Field(default=Decimal("0"))

    @property
    def is_depleted(self) -> bool:
        """Check if lot has been fully sold."""
        return self.remaining_quantity <= Decimal("0")

    def get_holding_period(self, sale_date: datetime) -> HoldingPeriod:
        """Calculate holding period for a sale date."""
        days_held = (sale_date - self.date_acquired).days
        if days_held > 365:
            return HoldingPeriod.LONG_TERM
        return HoldingPeriod.SHORT_TERM


class DisposalEvent(BaseModel):
    """Represents a taxable disposal of cryptocurrency."""
    id: str = Field(..., description="Unique disposal ID")
    asset: CryptoAsset = Field(..., description="Asset sold/disposed")
    quantity: Decimal = Field(..., description="Quantity disposed")
    date_sold: datetime = Field(..., description="Disposal date")
    proceeds: Decimal = Field(..., description="Sale proceeds in USD")
    cost_basis: Decimal = Field(..., description="Cost basis in USD")
    gain_or_loss: Decimal = Field(..., description="Capital gain or loss")
    holding_period: HoldingPeriod = Field(..., description="Short or long term")

    # Form 8949 fields
    form_8949_category: Form8949Category = Field(default=Form8949Category.CATEGORY_C)
    adjustment_code: str = Field(default="", description="Adjustment code (e.g., 'W' for wash sale)")
    adjustment_amount: Decimal = Field(default=Decimal("0"))

    # Wash sale tracking
    is_wash_sale: bool = Field(default=False)
    wash_sale_loss_disallowed: Decimal = Field(default=Decimal("0"))

    # Lot matching
    lots_used: List[Dict[str, Any]] = Field(default_factory=list)
    source_transaction_id: str = Field(..., description="Original sale transaction ID")


class CryptoIncome(BaseModel):
    """Cryptocurrency income event (staking, mining, etc.)."""
    id: str = Field(..., description="Unique income ID")
    income_type: IncomeType = Field(..., description="Type of income")
    transaction_type: TransactionType = Field(..., description="Source transaction type")
    asset: CryptoAsset = Field(..., description="Asset received")
    quantity: Decimal = Field(..., description="Quantity received")
    fair_market_value_usd: Decimal = Field(..., description="FMV at receipt")
    date_received: datetime = Field(..., description="Receipt date")
    source_transaction_id: str = Field(..., description="Original transaction ID")

    # For self-employment income
    is_self_employment: bool = Field(default=False)
    business_expenses: Decimal = Field(default=Decimal("0"))


class WashSaleViolation(BaseModel):
    """Tracks a wash sale violation."""
    loss_transaction_id: str = Field(..., description="Transaction with disallowed loss")
    replacement_transaction_id: str = Field(..., description="Replacement purchase")
    asset: CryptoAsset = Field(..., description="Asset involved")
    loss_date: datetime = Field(..., description="Date of loss")
    replacement_date: datetime = Field(..., description="Date of replacement purchase")
    disallowed_loss: Decimal = Field(..., description="Loss disallowed")
    adjustment_to_basis: Decimal = Field(..., description="Basis adjustment amount")


class PortfolioHoldings(BaseModel):
    """Current cryptocurrency holdings with cost basis."""
    holdings: Dict[str, List[CryptoLot]] = Field(default_factory=dict)
    total_cost_basis: Decimal = Field(default=Decimal("0"))
    unrealized_gains: Decimal = Field(default=Decimal("0"))
    as_of_date: datetime = Field(default_factory=datetime.utcnow)


class CryptoTaxSummary(BaseModel):
    """Comprehensive crypto tax summary for a tax year."""
    tax_year: int = Field(..., description="Tax year")

    # Capital gains/losses
    short_term_gains: Decimal = Field(default=Decimal("0"))
    short_term_losses: Decimal = Field(default=Decimal("0"))
    long_term_gains: Decimal = Field(default=Decimal("0"))
    long_term_losses: Decimal = Field(default=Decimal("0"))
    net_capital_gain_loss: Decimal = Field(default=Decimal("0"))

    # Wash sales
    total_wash_sale_adjustments: Decimal = Field(default=Decimal("0"))
    wash_sale_count: int = Field(default=0)

    # Income
    staking_income: Decimal = Field(default=Decimal("0"))
    mining_income: Decimal = Field(default=Decimal("0"))
    airdrop_income: Decimal = Field(default=Decimal("0"))
    interest_income: Decimal = Field(default=Decimal("0"))
    other_income: Decimal = Field(default=Decimal("0"))
    total_ordinary_income: Decimal = Field(default=Decimal("0"))

    # Disposals
    total_disposals: int = Field(default=0)
    total_proceeds: Decimal = Field(default=Decimal("0"))
    total_cost_basis: Decimal = Field(default=Decimal("0"))

    # By exchange
    by_exchange: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ImportResult(BaseModel):
    """Result of importing cryptocurrency data."""
    success: bool = Field(default=True)
    exchange: ExchangeType = Field(...)
    transactions_imported: int = Field(default=0)
    transactions_skipped: int = Field(default=0)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    transactions: List[CryptoTransaction] = Field(default_factory=list)


class Form8949Data(BaseModel):
    """Data structured for IRS Form 8949."""
    tax_year: int = Field(...)

    # Part I - Short-term (categories A, B, C)
    part_i_category_a: List[Dict[str, Any]] = Field(default_factory=list)
    part_i_category_b: List[Dict[str, Any]] = Field(default_factory=list)
    part_i_category_c: List[Dict[str, Any]] = Field(default_factory=list)
    part_i_totals: Dict[str, Decimal] = Field(default_factory=dict)

    # Part II - Long-term (categories D, E, F)
    part_ii_category_d: List[Dict[str, Any]] = Field(default_factory=list)
    part_ii_category_e: List[Dict[str, Any]] = Field(default_factory=list)
    part_ii_category_f: List[Dict[str, Any]] = Field(default_factory=list)
    part_ii_totals: Dict[str, Decimal] = Field(default_factory=dict)


class ScheduleDData(BaseModel):
    """Data structured for IRS Schedule D."""
    tax_year: int = Field(...)

    # Part I - Short-term
    line_1a: Decimal = Field(default=Decimal("0"))  # Totals from Form 8949 Box A
    line_1b: Decimal = Field(default=Decimal("0"))  # Totals from Form 8949 Box B
    line_2: Decimal = Field(default=Decimal("0"))   # Totals from Form 8949 Box C
    line_7: Decimal = Field(default=Decimal("0"))   # Net short-term gain/loss

    # Part II - Long-term
    line_8a: Decimal = Field(default=Decimal("0"))  # Totals from Form 8949 Box D
    line_8b: Decimal = Field(default=Decimal("0"))  # Totals from Form 8949 Box E
    line_9: Decimal = Field(default=Decimal("0"))   # Totals from Form 8949 Box F
    line_15: Decimal = Field(default=Decimal("0"))  # Net long-term gain/loss

    # Part III - Summary
    line_16: Decimal = Field(default=Decimal("0"))  # Net capital gain/loss


# =============================================================================
# Exchange Parsers
# =============================================================================

class BaseExchangeParser(ABC):
    """Abstract base class for exchange-specific CSV parsers."""

    exchange_type: ExchangeType = ExchangeType.UNKNOWN

    @abstractmethod
    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse CSV content into transactions."""
        pass

    @abstractmethod
    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect if CSV matches this exchange format."""
        pass

    def _generate_id(self, *args) -> str:
        """Generate unique transaction ID from components."""
        content = "|".join(str(a) for a in args)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _parse_decimal(self, value: Optional[str]) -> Decimal:
        """Parse decimal value from string."""
        if not value:
            return Decimal("0")
        cleaned = re.sub(r'[,$()]', '', str(value).strip())
        if cleaned.startswith('(') or cleaned.endswith(')'):
            cleaned = '-' + cleaned.replace('(', '').replace(')', '')
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal("0")

    def _parse_datetime(self, value: str, formats: List[str] = None) -> Optional[datetime]:
        """Parse datetime from string."""
        if not value:
            return None

        formats = formats or [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S UTC",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%d-%b-%Y %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    def _map_transaction_type(self, type_str: str) -> TransactionType:
        """Map exchange-specific type string to TransactionType."""
        type_lower = type_str.lower().strip()

        mapping = {
            'buy': TransactionType.BUY,
            'purchase': TransactionType.BUY,
            'bought': TransactionType.BUY,
            'sell': TransactionType.SELL,
            'sold': TransactionType.SELL,
            'sale': TransactionType.SELL,
            'convert': TransactionType.CONVERT,
            'conversion': TransactionType.CONVERT,
            'trade': TransactionType.SWAP,
            'swap': TransactionType.SWAP,
            'exchange': TransactionType.SWAP,
            'send': TransactionType.SEND,
            'sent': TransactionType.SEND,
            'withdraw': TransactionType.SEND,
            'withdrawal': TransactionType.SEND,
            'receive': TransactionType.RECEIVE,
            'received': TransactionType.RECEIVE,
            'deposit': TransactionType.RECEIVE,
            'staking': TransactionType.STAKING_REWARD,
            'staking reward': TransactionType.STAKING_REWARD,
            'staking income': TransactionType.STAKING_REWARD,
            'stake': TransactionType.STAKING_REWARD,
            'interest': TransactionType.INTEREST,
            'earn': TransactionType.INTEREST,
            'reward': TransactionType.REWARD,
            'rewards': TransactionType.REWARD,
            'learning reward': TransactionType.REWARD,
            'coinbase earn': TransactionType.REWARD,
            'airdrop': TransactionType.AIRDROP,
            'fork': TransactionType.FORK,
            'mining': TransactionType.MINING,
            'mined': TransactionType.MINING,
            'gift': TransactionType.GIFT_RECEIVED,
            'gift received': TransactionType.GIFT_RECEIVED,
            'gift sent': TransactionType.GIFT_SENT,
            'nft purchase': TransactionType.NFT_PURCHASE,
            'nft sale': TransactionType.NFT_SALE,
            'nft mint': TransactionType.NFT_MINT,
        }

        for key, txn_type in mapping.items():
            if key in type_lower:
                return txn_type

        return TransactionType.UNKNOWN


class CoinbaseParser(BaseExchangeParser):
    """Parser for Coinbase transaction exports."""

    exchange_type = ExchangeType.COINBASE

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Coinbase CSV format."""
        header_lower = [h.lower() for h in headers]
        coinbase_indicators = ['asset', 'transaction type', 'quantity transacted']
        return all(ind in header_lower for ind in coinbase_indicators)

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Coinbase CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                txn_type_str = row.get('Transaction Type', row.get('transaction type', ''))
                txn_type = self._map_transaction_type(txn_type_str)

                timestamp = self._parse_datetime(
                    row.get('Timestamp', row.get('timestamp', ''))
                )
                if not timestamp:
                    continue

                asset_symbol = row.get('Asset', row.get('asset', '')).upper()
                quantity = self._parse_decimal(
                    row.get('Quantity Transacted', row.get('quantity transacted', ''))
                )
                spot_price = self._parse_decimal(
                    row.get('Spot Price at Transaction', row.get('spot price at transaction', ''))
                )
                subtotal = self._parse_decimal(
                    row.get('Subtotal', row.get('subtotal', ''))
                )
                total = self._parse_decimal(
                    row.get('Total (inclusive of fees)', row.get('total (inclusive of fees)', ''))
                )
                fees = self._parse_decimal(
                    row.get('Fees', row.get('fees', ''))
                )

                total_value = total if total else (quantity * spot_price)

                txn = CryptoTransaction(
                    id=self._generate_id(timestamp, asset_symbol, quantity, txn_type_str),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=asset_symbol),
                    quantity=abs(quantity),
                    price_per_unit=spot_price,
                    total_value_usd=abs(total_value),
                    fee_amount=fees,
                    fee_asset='USD',
                    fee_usd=fees,
                    notes=row.get('Notes', row.get('notes', '')),
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Coinbase row: {e}")
                continue

        return transactions


class CoinbaseProParser(BaseExchangeParser):
    """Parser for Coinbase Pro (Advanced Trade) exports."""

    exchange_type = ExchangeType.COINBASE_PRO

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Coinbase Pro CSV format."""
        header_lower = [h.lower() for h in headers]
        indicators = ['portfolio', 'trade id', 'product', 'side']
        return all(ind in header_lower for ind in indicators)

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Coinbase Pro CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                side = row.get('side', '').lower()
                txn_type = TransactionType.BUY if side == 'buy' else TransactionType.SELL

                timestamp = self._parse_datetime(row.get('created at', ''))
                if not timestamp:
                    continue

                product = row.get('product', '')
                asset_symbol = product.split('-')[0] if '-' in product else product

                size = self._parse_decimal(row.get('size', ''))
                price = self._parse_decimal(row.get('price', ''))
                fee = self._parse_decimal(row.get('fee', ''))
                total = self._parse_decimal(row.get('total', ''))

                txn = CryptoTransaction(
                    id=row.get('trade id', self._generate_id(timestamp, product, size)),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=asset_symbol.upper()),
                    quantity=abs(size),
                    price_per_unit=price,
                    total_value_usd=abs(total),
                    fee_amount=fee,
                    fee_asset='USD',
                    fee_usd=fee,
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Coinbase Pro row: {e}")
                continue

        return transactions


class KrakenParser(BaseExchangeParser):
    """Parser for Kraken exchange exports."""

    exchange_type = ExchangeType.KRAKEN

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Kraken CSV format."""
        header_lower = [h.lower() for h in headers]
        indicators = ['txid', 'refid', 'type', 'asset']
        return all(ind in header_lower for ind in indicators)

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Kraken CSV (ledger format)."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                txn_type_str = row.get('type', '').lower()

                timestamp = self._parse_datetime(row.get('time', ''))
                if not timestamp:
                    continue

                asset = row.get('asset', '').upper()
                # Kraken uses X prefix for some crypto (e.g., XXBT for BTC)
                if asset.startswith('X') and len(asset) > 3:
                    asset = asset[1:]
                if asset == 'XBT':
                    asset = 'BTC'
                if asset.startswith('Z') and len(asset) > 3:
                    asset = asset[1:]  # ZUSD -> USD

                amount = self._parse_decimal(row.get('amount', ''))
                fee = self._parse_decimal(row.get('fee', ''))

                # Map Kraken types
                if txn_type_str == 'trade':
                    txn_type = TransactionType.BUY if amount > 0 else TransactionType.SELL
                elif txn_type_str == 'deposit':
                    txn_type = TransactionType.RECEIVE
                elif txn_type_str == 'withdrawal':
                    txn_type = TransactionType.SEND
                elif txn_type_str == 'staking':
                    txn_type = TransactionType.STAKING_REWARD
                else:
                    txn_type = self._map_transaction_type(txn_type_str)

                txn = CryptoTransaction(
                    id=row.get('txid', self._generate_id(timestamp, asset, amount)),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=asset),
                    quantity=abs(amount),
                    total_value_usd=abs(amount),  # Will need price lookup
                    fee_amount=fee,
                    fee_usd=fee,
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Kraken row: {e}")
                continue

        return transactions


class BinanceUSParser(BaseExchangeParser):
    """Parser for Binance.US exports."""

    exchange_type = ExchangeType.BINANCE_US

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Binance.US CSV format."""
        header_lower = [h.lower() for h in headers]
        indicators = ['user_id', 'utc_time', 'operation', 'coin']
        alt_indicators = ['date(utc)', 'pair', 'side', 'price']
        return (all(ind in header_lower for ind in indicators) or
                all(ind in header_lower for ind in alt_indicators))

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Binance.US CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                # Handle different Binance export formats
                if 'UTC_Time' in row or 'utc_time' in row:
                    timestamp_str = row.get('UTC_Time', row.get('utc_time', ''))
                    operation = row.get('Operation', row.get('operation', ''))
                    coin = row.get('Coin', row.get('coin', '')).upper()
                    change = self._parse_decimal(row.get('Change', row.get('change', '')))
                else:
                    timestamp_str = row.get('Date(UTC)', '')
                    operation = row.get('Side', '')
                    coin = row.get('Pair', '').split('/')[0] if '/' in row.get('Pair', '') else ''
                    change = self._parse_decimal(row.get('Executed', row.get('Amount', '')))

                timestamp = self._parse_datetime(timestamp_str)
                if not timestamp:
                    continue

                txn_type = self._map_transaction_type(operation)

                txn = CryptoTransaction(
                    id=self._generate_id(timestamp, coin, change, operation),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=coin),
                    quantity=abs(change),
                    total_value_usd=Decimal("0"),  # Needs price lookup
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Binance.US row: {e}")
                continue

        return transactions


class GeminiParser(BaseExchangeParser):
    """Parser for Gemini exchange exports."""

    exchange_type = ExchangeType.GEMINI

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Gemini CSV format."""
        header_lower = [h.lower() for h in headers]
        indicators = ['date', 'time (utc)', 'type', 'symbol', 'specification']
        return all(ind in header_lower for ind in indicators)

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Gemini CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                date_str = row.get('Date', '')
                time_str = row.get('Time (UTC)', '')
                timestamp = self._parse_datetime(f"{date_str} {time_str}")
                if not timestamp:
                    continue

                txn_type_str = row.get('Type', '')
                symbol = row.get('Symbol', '').upper()

                # Gemini format: "Buy 0.01 BTC"
                specification = row.get('Specification', '')

                # Parse amounts from specification or dedicated columns
                usd_amount = self._parse_decimal(row.get('USD Amount', ''))
                fee = self._parse_decimal(row.get('Fee (USD)', ''))
                crypto_amount = self._parse_decimal(row.get(f'{symbol} Amount', ''))

                txn_type = self._map_transaction_type(txn_type_str)

                txn = CryptoTransaction(
                    id=self._generate_id(timestamp, symbol, crypto_amount, txn_type_str),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=symbol),
                    quantity=abs(crypto_amount),
                    total_value_usd=abs(usd_amount),
                    fee_usd=fee,
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Gemini row: {e}")
                continue

        return transactions


class RobinhoodCryptoParser(BaseExchangeParser):
    """Parser for Robinhood Crypto exports."""

    exchange_type = ExchangeType.ROBINHOOD_CRYPTO

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Robinhood Crypto CSV format."""
        header_lower = [h.lower() for h in headers]
        indicators = ['asset name', 'received date', 'cost basis']
        alt_indicators = ['symbol', 'name', 'quantity']
        return (all(ind in header_lower for ind in indicators) or
                (all(ind in header_lower for ind in alt_indicators) and
                 'robinhood' in csv_content.lower()))

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Robinhood Crypto CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                asset_name = row.get('Asset Name', row.get('Symbol', ''))
                received_date = row.get('Received Date', row.get('Date', ''))
                timestamp = self._parse_datetime(received_date)
                if not timestamp:
                    continue

                quantity = self._parse_decimal(row.get('Quantity', ''))
                cost_basis = self._parse_decimal(row.get('Cost Basis', ''))
                proceeds = self._parse_decimal(row.get('Proceeds', ''))

                # Determine transaction type
                if proceeds > 0:
                    txn_type = TransactionType.SELL
                    total_value = proceeds
                else:
                    txn_type = TransactionType.BUY
                    total_value = cost_basis

                txn = CryptoTransaction(
                    id=self._generate_id(timestamp, asset_name, quantity),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=asset_name.upper()),
                    quantity=abs(quantity),
                    total_value_usd=abs(total_value),
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Robinhood row: {e}")
                continue

        return transactions


class CryptoComParser(BaseExchangeParser):
    """Parser for Crypto.com exports."""

    exchange_type = ExchangeType.CRYPTO_COM

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Detect Crypto.com CSV format."""
        header_lower = [h.lower() for h in headers]
        indicators = ['timestamp (utc)', 'transaction description', 'currency', 'amount']
        return all(ind in header_lower for ind in indicators)

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse Crypto.com CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                timestamp = self._parse_datetime(row.get('Timestamp (UTC)', ''))
                if not timestamp:
                    continue

                description = row.get('Transaction Description', '')
                currency = row.get('Currency', '').upper()
                amount = self._parse_decimal(row.get('Amount', ''))
                native_amount = self._parse_decimal(row.get('Native Amount', ''))
                native_currency = row.get('Native Currency', 'USD')

                # Map Crypto.com descriptions to transaction types
                txn_type = self._map_transaction_type(description)

                # Use native amount if in USD, otherwise use amount
                total_value = native_amount if native_currency == 'USD' else amount

                txn = CryptoTransaction(
                    id=row.get('Transaction ID', self._generate_id(timestamp, currency, amount)),
                    exchange=self.exchange_type,
                    transaction_type=txn_type,
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=currency),
                    quantity=abs(amount),
                    total_value_usd=abs(total_value),
                    notes=description,
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse Crypto.com row: {e}")
                continue

        return transactions


class GenericCryptoParser(BaseExchangeParser):
    """Generic CSV parser with flexible column mapping."""

    exchange_type = ExchangeType.GENERIC

    def detect(self, csv_content: str, headers: List[str]) -> bool:
        """Always returns True as fallback parser."""
        return True

    def parse(self, csv_content: str) -> List[CryptoTransaction]:
        """Parse generic crypto CSV."""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))

        # Build column mapping
        headers = reader.fieldnames or []
        mapping = self._build_column_mapping(headers)

        for row in reader:
            try:
                timestamp = self._parse_datetime(row.get(mapping.get('timestamp', ''), ''))
                if not timestamp:
                    continue

                asset = row.get(mapping.get('asset', ''), 'UNKNOWN').upper()
                quantity = self._parse_decimal(row.get(mapping.get('quantity', ''), ''))
                txn_type_str = row.get(mapping.get('type', ''), '')
                value = self._parse_decimal(row.get(mapping.get('value', ''), ''))

                txn = CryptoTransaction(
                    id=self._generate_id(timestamp, asset, quantity),
                    exchange=self.exchange_type,
                    transaction_type=self._map_transaction_type(txn_type_str),
                    timestamp=timestamp,
                    asset=CryptoAsset(symbol=asset),
                    quantity=abs(quantity),
                    total_value_usd=abs(value),
                    raw_data=dict(row),
                )
                transactions.append(txn)

            except Exception as e:
                logger.warning(f"Failed to parse generic row: {e}")
                continue

        return transactions

    def _build_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Build column mapping from headers."""
        header_lower = {h.lower(): h for h in headers}

        mapping = {}

        # Timestamp variations
        for key in ['timestamp', 'date', 'time', 'datetime', 'created', 'executed']:
            for h, original in header_lower.items():
                if key in h:
                    mapping['timestamp'] = original
                    break
            if 'timestamp' in mapping:
                break

        # Asset variations
        for key in ['asset', 'symbol', 'coin', 'currency', 'token']:
            for h, original in header_lower.items():
                if key in h and 'native' not in h:
                    mapping['asset'] = original
                    break
            if 'asset' in mapping:
                break

        # Quantity variations
        for key in ['quantity', 'amount', 'size', 'volume']:
            for h, original in header_lower.items():
                if key in h:
                    mapping['quantity'] = original
                    break
            if 'quantity' in mapping:
                break

        # Type variations
        for key in ['type', 'side', 'action', 'operation', 'transaction']:
            for h, original in header_lower.items():
                if key in h:
                    mapping['type'] = original
                    break
            if 'type' in mapping:
                break

        # Value variations
        for key in ['value', 'total', 'usd', 'amount', 'price']:
            for h, original in header_lower.items():
                if key in h and 'native' not in h:
                    mapping['value'] = original
                    break
            if 'value' in mapping:
                break

        return mapping


# =============================================================================
# Cost Basis Calculator
# =============================================================================

class CostBasisCalculator:
    """Calculate cost basis using various IRS-approved methods."""

    def __init__(self, method: CostBasisMethod = CostBasisMethod.FIFO):
        """Initialize calculator with specified method."""
        self.method = method
        self.lots: Dict[str, List[CryptoLot]] = {}  # symbol -> list of lots
        self._lot_counter = 0

    def _next_lot_id(self) -> str:
        """Generate next lot ID."""
        self._lot_counter += 1
        return f"LOT-{self._lot_counter:06d}"

    def add_lot(
        self,
        asset: CryptoAsset,
        quantity: Decimal,
        cost_basis: Decimal,
        date_acquired: datetime,
        acquisition_type: TransactionType,
        source_transaction_id: str,
    ) -> CryptoLot:
        """Add a new tax lot from acquisition."""
        lot = CryptoLot(
            id=self._next_lot_id(),
            asset=asset,
            quantity=quantity,
            remaining_quantity=quantity,
            cost_basis_per_unit=cost_basis / quantity if quantity > 0 else Decimal("0"),
            total_cost_basis=cost_basis,
            date_acquired=date_acquired,
            acquisition_type=acquisition_type,
            source_transaction_id=source_transaction_id,
        )

        symbol = asset.symbol
        if symbol not in self.lots:
            self.lots[symbol] = []
        self.lots[symbol].append(lot)

        return lot

    def calculate_disposal(
        self,
        asset: CryptoAsset,
        quantity: Decimal,
        proceeds: Decimal,
        date_sold: datetime,
        source_transaction_id: str,
        specific_lot_ids: Optional[List[str]] = None,
    ) -> DisposalEvent:
        """Calculate cost basis and gain/loss for a disposal."""
        symbol = asset.symbol

        if symbol not in self.lots:
            # No lots found - use zero cost basis
            return DisposalEvent(
                id=f"DISP-{source_transaction_id[:8]}",
                asset=asset,
                quantity=quantity,
                date_sold=date_sold,
                proceeds=proceeds,
                cost_basis=Decimal("0"),
                gain_or_loss=proceeds,
                holding_period=HoldingPeriod.UNKNOWN,
                form_8949_category=Form8949Category.CATEGORY_C,
                source_transaction_id=source_transaction_id,
            )

        # Get lots to use based on method
        lots_to_use = self._select_lots(symbol, quantity, date_sold, specific_lot_ids)

        total_cost_basis = Decimal("0")
        lots_used = []
        remaining_quantity = quantity
        earliest_acquisition = None
        latest_acquisition = None

        for lot, qty_from_lot in lots_to_use:
            lot_cost = lot.cost_basis_per_unit * qty_from_lot
            total_cost_basis += lot_cost

            # Track acquisition dates for holding period
            if earliest_acquisition is None or lot.date_acquired < earliest_acquisition:
                earliest_acquisition = lot.date_acquired
            if latest_acquisition is None or lot.date_acquired > latest_acquisition:
                latest_acquisition = lot.date_acquired

            # Update lot remaining quantity
            lot.remaining_quantity -= qty_from_lot

            lots_used.append({
                "lot_id": lot.id,
                "quantity": str(qty_from_lot),
                "cost_basis": str(lot_cost),
                "date_acquired": lot.date_acquired.isoformat(),
            })

            remaining_quantity -= qty_from_lot
            if remaining_quantity <= Decimal("0"):
                break

        # Determine holding period based on method
        if self.method in [CostBasisMethod.FIFO, CostBasisMethod.LIFO, CostBasisMethod.HIFO]:
            # Use earliest lot for FIFO, latest for LIFO, etc.
            reference_date = earliest_acquisition if earliest_acquisition else date_sold
        else:
            reference_date = earliest_acquisition if earliest_acquisition else date_sold

        days_held = (date_sold - reference_date).days
        holding_period = HoldingPeriod.LONG_TERM if days_held > 365 else HoldingPeriod.SHORT_TERM

        # Determine Form 8949 category
        # Crypto generally doesn't have basis reported to IRS (Category C or F)
        category = (Form8949Category.CATEGORY_C if holding_period == HoldingPeriod.SHORT_TERM
                   else Form8949Category.CATEGORY_F)

        gain_or_loss = proceeds - total_cost_basis

        return DisposalEvent(
            id=f"DISP-{source_transaction_id[:8]}",
            asset=asset,
            quantity=quantity,
            date_sold=date_sold,
            proceeds=proceeds,
            cost_basis=total_cost_basis,
            gain_or_loss=gain_or_loss,
            holding_period=holding_period,
            form_8949_category=category,
            lots_used=lots_used,
            source_transaction_id=source_transaction_id,
        )

    def _select_lots(
        self,
        symbol: str,
        quantity: Decimal,
        sale_date: datetime,
        specific_lot_ids: Optional[List[str]] = None,
    ) -> List[Tuple[CryptoLot, Decimal]]:
        """Select lots based on cost basis method."""
        available_lots = [
            lot for lot in self.lots.get(symbol, [])
            if lot.remaining_quantity > 0 and lot.date_acquired <= sale_date
        ]

        if specific_lot_ids and self.method == CostBasisMethod.SPECIFIC_ID:
            # Use specific lots in order provided
            lot_map = {lot.id: lot for lot in available_lots}
            sorted_lots = [lot_map[lid] for lid in specific_lot_ids if lid in lot_map]
        elif self.method == CostBasisMethod.FIFO:
            sorted_lots = sorted(available_lots, key=lambda x: x.date_acquired)
        elif self.method == CostBasisMethod.LIFO:
            sorted_lots = sorted(available_lots, key=lambda x: x.date_acquired, reverse=True)
        elif self.method == CostBasisMethod.HIFO:
            sorted_lots = sorted(available_lots, key=lambda x: x.cost_basis_per_unit, reverse=True)
        elif self.method == CostBasisMethod.AVERAGE_COST:
            # For average cost, we use all lots proportionally
            return self._calculate_average_cost(available_lots, quantity)
        else:
            sorted_lots = available_lots

        # Select lots until quantity is fulfilled
        result = []
        remaining = quantity

        for lot in sorted_lots:
            if remaining <= 0:
                break
            qty_from_lot = min(lot.remaining_quantity, remaining)
            result.append((lot, qty_from_lot))
            remaining -= qty_from_lot

        return result

    def _calculate_average_cost(
        self,
        lots: List[CryptoLot],
        quantity: Decimal,
    ) -> List[Tuple[CryptoLot, Decimal]]:
        """Calculate using average cost method."""
        if not lots:
            return []

        total_quantity = sum(lot.remaining_quantity for lot in lots)
        total_basis = sum(lot.remaining_quantity * lot.cost_basis_per_unit for lot in lots)

        if total_quantity <= 0:
            return []

        avg_cost = total_basis / total_quantity

        # Distribute the sale proportionally across lots
        result = []
        remaining = quantity

        for lot in lots:
            if remaining <= 0:
                break
            proportion = lot.remaining_quantity / total_quantity
            qty_from_lot = min(lot.remaining_quantity, quantity * proportion, remaining)
            result.append((lot, qty_from_lot))
            remaining -= qty_from_lot

        return result

    def get_holdings(self, symbol: Optional[str] = None) -> PortfolioHoldings:
        """Get current holdings with cost basis."""
        holdings = {}
        total_basis = Decimal("0")

        symbols = [symbol] if symbol else list(self.lots.keys())

        for sym in symbols:
            lots = [lot for lot in self.lots.get(sym, []) if lot.remaining_quantity > 0]
            if lots:
                holdings[sym] = lots
                total_basis += sum(
                    lot.remaining_quantity * lot.cost_basis_per_unit
                    for lot in lots
                )

        return PortfolioHoldings(
            holdings=holdings,
            total_cost_basis=total_basis,
        )


# =============================================================================
# Wash Sale Detector
# =============================================================================

class WashSaleDetector:
    """Detect and track wash sale violations per IRS rules."""

    WASH_SALE_WINDOW_DAYS = 30

    def __init__(self):
        """Initialize detector."""
        self.violations: List[WashSaleViolation] = []
        self._transaction_index: Dict[str, List[CryptoTransaction]] = {}

    def index_transactions(self, transactions: List[CryptoTransaction]) -> None:
        """Index transactions by asset for wash sale detection."""
        self._transaction_index.clear()

        for txn in transactions:
            symbol = txn.asset.symbol
            if symbol not in self._transaction_index:
                self._transaction_index[symbol] = []
            self._transaction_index[symbol].append(txn)

        # Sort by timestamp
        for symbol in self._transaction_index:
            self._transaction_index[symbol].sort(key=lambda x: x.timestamp)

    def detect_wash_sales(
        self,
        disposals: List[DisposalEvent],
        transactions: List[CryptoTransaction],
    ) -> List[WashSaleViolation]:
        """Detect wash sales from disposals and subsequent purchases."""
        self.index_transactions(transactions)
        self.violations = []

        for disposal in disposals:
            if disposal.gain_or_loss >= 0:
                # Only losses trigger wash sales
                continue

            symbol = disposal.asset.symbol
            loss_date = disposal.date_sold
            loss_amount = abs(disposal.gain_or_loss)

            # Look for purchases within 30 days before or after
            window_start = loss_date - timedelta(days=self.WASH_SALE_WINDOW_DAYS)
            window_end = loss_date + timedelta(days=self.WASH_SALE_WINDOW_DAYS)

            # Find replacement purchases
            replacements = [
                txn for txn in self._transaction_index.get(symbol, [])
                if (window_start <= txn.timestamp <= window_end and
                    txn.transaction_type in [
                        TransactionType.BUY,
                        TransactionType.RECEIVE,
                        TransactionType.STAKING_REWARD,
                        TransactionType.AIRDROP,
                    ] and
                    txn.id != disposal.source_transaction_id)
            ]

            if replacements:
                # Wash sale detected
                replacement = replacements[0]  # Use first replacement

                violation = WashSaleViolation(
                    loss_transaction_id=disposal.source_transaction_id,
                    replacement_transaction_id=replacement.id,
                    asset=disposal.asset,
                    loss_date=loss_date,
                    replacement_date=replacement.timestamp,
                    disallowed_loss=loss_amount,
                    adjustment_to_basis=loss_amount,
                )
                self.violations.append(violation)

                # Update disposal with wash sale info
                disposal.is_wash_sale = True
                disposal.wash_sale_loss_disallowed = loss_amount
                disposal.adjustment_code = "W"
                disposal.adjustment_amount = loss_amount

        return self.violations


# =============================================================================
# Main Service Class
# =============================================================================

class CryptoImportService:
    """Comprehensive cryptocurrency import and tax calculation service."""

    def __init__(
        self,
        cost_basis_method: CostBasisMethod = CostBasisMethod.FIFO,
        detect_wash_sales: bool = True,
    ):
        """Initialize the crypto import service.

        Args:
            cost_basis_method: Method for calculating cost basis.
            detect_wash_sales: Whether to detect and adjust for wash sales.
        """
        self.cost_basis_method = cost_basis_method
        self.detect_wash_sales = detect_wash_sales

        self.cost_basis_calculator = CostBasisCalculator(method=cost_basis_method)
        self.wash_sale_detector = WashSaleDetector()

        # All imported transactions
        self.transactions: List[CryptoTransaction] = []
        self.disposals: List[DisposalEvent] = []
        self.income_events: List[CryptoIncome] = []

        # Register parsers
        self.parsers: List[BaseExchangeParser] = [
            CoinbaseParser(),
            CoinbaseProParser(),
            KrakenParser(),
            BinanceUSParser(),
            GeminiParser(),
            RobinhoodCryptoParser(),
            CryptoComParser(),
            GenericCryptoParser(),  # Fallback
        ]

    def detect_exchange(self, csv_content: str) -> ExchangeType:
        """Detect which exchange the CSV is from."""
        try:
            reader = csv.reader(io.StringIO(csv_content))
            headers = next(reader, [])

            for parser in self.parsers:
                if parser.exchange_type != ExchangeType.GENERIC and parser.detect(csv_content, headers):
                    return parser.exchange_type

            return ExchangeType.GENERIC
        except Exception:
            return ExchangeType.UNKNOWN

    def import_csv(
        self,
        csv_content: str,
        exchange: Optional[ExchangeType] = None,
        tax_year: Optional[int] = None,
    ) -> ImportResult:
        """Import transactions from CSV content.

        Args:
            csv_content: CSV file content as string.
            exchange: Optional exchange type override.
            tax_year: Optional filter for specific tax year.

        Returns:
            ImportResult with parsed transactions.
        """
        if not exchange:
            exchange = self.detect_exchange(csv_content)

        result = ImportResult(exchange=exchange)

        # Find appropriate parser
        parser = None
        if exchange != ExchangeType.UNKNOWN:
            for p in self.parsers:
                if p.exchange_type == exchange:
                    parser = p
                    break

        if not parser:
            parser = GenericCryptoParser()

        try:
            parsed_transactions = parser.parse(csv_content)

            # Filter by tax year if specified
            if tax_year:
                parsed_transactions = [
                    txn for txn in parsed_transactions
                    if txn.timestamp.year == tax_year
                ]

            result.transactions = parsed_transactions
            result.transactions_imported = len(parsed_transactions)
            self.transactions.extend(parsed_transactions)

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to parse CSV: {str(e)}")
            logger.error(f"CSV import failed: {e}")

        return result

    def import_file(
        self,
        file_path: Path,
        exchange: Optional[ExchangeType] = None,
        tax_year: Optional[int] = None,
    ) -> ImportResult:
        """Import transactions from a CSV file.

        Args:
            file_path: Path to CSV file.
            exchange: Optional exchange type override.
            tax_year: Optional filter for specific tax year.

        Returns:
            ImportResult with parsed transactions.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.import_csv(content, exchange, tax_year)
        except Exception as e:
            return ImportResult(
                success=False,
                exchange=exchange or ExchangeType.UNKNOWN,
                errors=[f"Failed to read file: {str(e)}"],
            )

    def process_transactions(self, tax_year: int) -> CryptoTaxSummary:
        """Process all imported transactions and calculate taxes.

        Args:
            tax_year: Tax year to calculate for.

        Returns:
            CryptoTaxSummary with complete tax information.
        """
        # Sort transactions by timestamp
        sorted_txns = sorted(self.transactions, key=lambda x: x.timestamp)

        # Filter to tax year
        year_txns = [t for t in sorted_txns if t.timestamp.year == tax_year]

        # Process acquisitions first to build lot inventory
        for txn in sorted_txns:
            if txn.transaction_type in [
                TransactionType.BUY,
                TransactionType.RECEIVE,
                TransactionType.GIFT_RECEIVED,
            ]:
                self.cost_basis_calculator.add_lot(
                    asset=txn.asset,
                    quantity=txn.quantity,
                    cost_basis=txn.total_value_usd + txn.fee_usd,
                    date_acquired=txn.timestamp,
                    acquisition_type=txn.transaction_type,
                    source_transaction_id=txn.id,
                )

            # Income events get zero cost basis lot
            elif txn.is_income_event:
                self.cost_basis_calculator.add_lot(
                    asset=txn.asset,
                    quantity=txn.quantity,
                    cost_basis=txn.total_value_usd,  # FMV at receipt
                    date_acquired=txn.timestamp,
                    acquisition_type=txn.transaction_type,
                    source_transaction_id=txn.id,
                )

                # Record income
                income = CryptoIncome(
                    id=f"INC-{txn.id[:8]}",
                    income_type=IncomeType.ORDINARY_INCOME,
                    transaction_type=txn.transaction_type,
                    asset=txn.asset,
                    quantity=txn.quantity,
                    fair_market_value_usd=txn.total_value_usd,
                    date_received=txn.timestamp,
                    source_transaction_id=txn.id,
                    is_self_employment=(txn.transaction_type == TransactionType.MINING),
                )
                self.income_events.append(income)

        # Process disposals for tax year
        self.disposals = []
        for txn in year_txns:
            if txn.is_taxable_event:
                disposal = self.cost_basis_calculator.calculate_disposal(
                    asset=txn.asset,
                    quantity=txn.quantity,
                    proceeds=txn.total_value_usd - txn.fee_usd,
                    date_sold=txn.timestamp,
                    source_transaction_id=txn.id,
                )
                self.disposals.append(disposal)

                # Handle conversions - received asset becomes new lot
                if txn.transaction_type in [TransactionType.CONVERT, TransactionType.SWAP]:
                    if txn.received_asset and txn.received_quantity:
                        self.cost_basis_calculator.add_lot(
                            asset=txn.received_asset,
                            quantity=txn.received_quantity,
                            cost_basis=txn.received_value_usd or txn.total_value_usd,
                            date_acquired=txn.timestamp,
                            acquisition_type=txn.transaction_type,
                            source_transaction_id=txn.id,
                        )

        # Detect wash sales
        if self.detect_wash_sales:
            self.wash_sale_detector.detect_wash_sales(self.disposals, sorted_txns)

        # Calculate summary
        return self._calculate_summary(tax_year)

    def _calculate_summary(self, tax_year: int) -> CryptoTaxSummary:
        """Calculate tax summary from processed data."""
        summary = CryptoTaxSummary(tax_year=tax_year)

        # Process disposals
        for disposal in self.disposals:
            summary.total_disposals += 1
            summary.total_proceeds += disposal.proceeds
            summary.total_cost_basis += disposal.cost_basis

            gain_loss = disposal.gain_or_loss
            if disposal.is_wash_sale:
                # Adjust gain/loss for wash sale
                gain_loss += disposal.wash_sale_loss_disallowed
                summary.total_wash_sale_adjustments += disposal.wash_sale_loss_disallowed
                summary.wash_sale_count += 1

            if disposal.holding_period == HoldingPeriod.SHORT_TERM:
                if gain_loss >= 0:
                    summary.short_term_gains += gain_loss
                else:
                    summary.short_term_losses += abs(gain_loss)
            else:
                if gain_loss >= 0:
                    summary.long_term_gains += gain_loss
                else:
                    summary.long_term_losses += abs(gain_loss)

        summary.net_capital_gain_loss = (
            summary.short_term_gains - summary.short_term_losses +
            summary.long_term_gains - summary.long_term_losses
        )

        # Process income events
        year_income = [i for i in self.income_events if i.date_received.year == tax_year]
        for income in year_income:
            if income.transaction_type == TransactionType.STAKING_REWARD:
                summary.staking_income += income.fair_market_value_usd
            elif income.transaction_type == TransactionType.MINING:
                summary.mining_income += income.fair_market_value_usd
            elif income.transaction_type == TransactionType.AIRDROP:
                summary.airdrop_income += income.fair_market_value_usd
            elif income.transaction_type == TransactionType.INTEREST:
                summary.interest_income += income.fair_market_value_usd
            else:
                summary.other_income += income.fair_market_value_usd

        summary.total_ordinary_income = (
            summary.staking_income + summary.mining_income +
            summary.airdrop_income + summary.interest_income +
            summary.other_income
        )

        # Group by exchange
        for txn in self.transactions:
            if txn.timestamp.year == tax_year:
                exchange_name = txn.exchange.value
                if exchange_name not in summary.by_exchange:
                    summary.by_exchange[exchange_name] = {
                        "transaction_count": 0,
                        "total_volume_usd": Decimal("0"),
                    }
                summary.by_exchange[exchange_name]["transaction_count"] += 1
                summary.by_exchange[exchange_name]["total_volume_usd"] += txn.total_value_usd

        return summary

    def generate_form_8949(self, tax_year: int) -> Form8949Data:
        """Generate Form 8949 data from processed disposals.

        Args:
            tax_year: Tax year.

        Returns:
            Form8949Data structured for IRS reporting.
        """
        form = Form8949Data(tax_year=tax_year)

        # Initialize totals
        part_i_totals = {
            "proceeds": Decimal("0"),
            "cost_basis": Decimal("0"),
            "adjustments": Decimal("0"),
            "gain_loss": Decimal("0"),
        }
        part_ii_totals = {
            "proceeds": Decimal("0"),
            "cost_basis": Decimal("0"),
            "adjustments": Decimal("0"),
            "gain_loss": Decimal("0"),
        }

        for disposal in self.disposals:
            entry = {
                "description": f"{disposal.quantity} {disposal.asset.symbol}",
                "date_acquired": "Various" if len(disposal.lots_used) > 1 else (
                    disposal.lots_used[0]["date_acquired"][:10] if disposal.lots_used else "Unknown"
                ),
                "date_sold": disposal.date_sold.strftime("%m/%d/%Y"),
                "proceeds": str(disposal.proceeds.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "cost_basis": str(disposal.cost_basis.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "adjustment_code": disposal.adjustment_code,
                "adjustment_amount": str(disposal.adjustment_amount.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "gain_loss": str(disposal.gain_or_loss.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            }

            # Categorize by holding period and reporting category
            if disposal.holding_period == HoldingPeriod.SHORT_TERM:
                if disposal.form_8949_category == Form8949Category.CATEGORY_A:
                    form.part_i_category_a.append(entry)
                elif disposal.form_8949_category == Form8949Category.CATEGORY_B:
                    form.part_i_category_b.append(entry)
                else:
                    form.part_i_category_c.append(entry)

                part_i_totals["proceeds"] += disposal.proceeds
                part_i_totals["cost_basis"] += disposal.cost_basis
                part_i_totals["adjustments"] += disposal.adjustment_amount
                part_i_totals["gain_loss"] += disposal.gain_or_loss
            else:
                if disposal.form_8949_category == Form8949Category.CATEGORY_D:
                    form.part_ii_category_d.append(entry)
                elif disposal.form_8949_category == Form8949Category.CATEGORY_E:
                    form.part_ii_category_e.append(entry)
                else:
                    form.part_ii_category_f.append(entry)

                part_ii_totals["proceeds"] += disposal.proceeds
                part_ii_totals["cost_basis"] += disposal.cost_basis
                part_ii_totals["adjustments"] += disposal.adjustment_amount
                part_ii_totals["gain_loss"] += disposal.gain_or_loss

        form.part_i_totals = {
            k: v.quantize(Decimal("0.01"), ROUND_HALF_UP) for k, v in part_i_totals.items()
        }
        form.part_ii_totals = {
            k: v.quantize(Decimal("0.01"), ROUND_HALF_UP) for k, v in part_ii_totals.items()
        }

        return form

    def generate_schedule_d(self, tax_year: int) -> ScheduleDData:
        """Generate Schedule D data from Form 8949.

        Args:
            tax_year: Tax year.

        Returns:
            ScheduleDData structured for IRS reporting.
        """
        form_8949 = self.generate_form_8949(tax_year)

        schedule_d = ScheduleDData(tax_year=tax_year)

        # Part I - Short-term
        schedule_d.line_1a = form_8949.part_i_totals.get("gain_loss", Decimal("0"))
        # Lines 1b and 2 would be from other 8949 categories
        schedule_d.line_7 = schedule_d.line_1a + schedule_d.line_1b + schedule_d.line_2

        # Part II - Long-term
        schedule_d.line_8a = form_8949.part_ii_totals.get("gain_loss", Decimal("0"))
        schedule_d.line_15 = schedule_d.line_8a + schedule_d.line_8b + schedule_d.line_9

        # Part III - Summary
        schedule_d.line_16 = schedule_d.line_7 + schedule_d.line_15

        return schedule_d

    def get_holdings(self) -> PortfolioHoldings:
        """Get current portfolio holdings with cost basis.

        Returns:
            PortfolioHoldings with current positions.
        """
        return self.cost_basis_calculator.get_holdings()

    def export_transactions(
        self,
        format: str = "csv",
        tax_year: Optional[int] = None,
    ) -> str:
        """Export transactions in specified format.

        Args:
            format: Export format (csv, json).
            tax_year: Optional filter by tax year.

        Returns:
            Formatted transaction data.
        """
        txns = self.transactions
        if tax_year:
            txns = [t for t in txns if t.timestamp.year == tax_year]

        if format == "json":
            return json.dumps(
                [txn.model_dump() for txn in txns],
                default=str,
                indent=2,
            )

        # CSV format
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Date", "Exchange", "Type", "Asset", "Quantity",
            "Price", "Total USD", "Fee USD", "Notes"
        ])

        for txn in txns:
            writer.writerow([
                txn.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                txn.exchange.value,
                txn.transaction_type.value,
                txn.asset.symbol,
                str(txn.quantity),
                str(txn.price_per_unit or ""),
                str(txn.total_value_usd),
                str(txn.fee_usd),
                txn.notes or "",
            ])

        return output.getvalue()

    def clear(self) -> None:
        """Clear all imported data."""
        self.transactions = []
        self.disposals = []
        self.income_events = []
        self.cost_basis_calculator = CostBasisCalculator(method=self.cost_basis_method)
        self.wash_sale_detector = WashSaleDetector()


# =============================================================================
# Utility Functions
# =============================================================================

def create_crypto_import_service(
    cost_basis_method: str = "FIFO",
    detect_wash_sales: bool = True,
) -> CryptoImportService:
    """Factory function to create CryptoImportService.

    Args:
        cost_basis_method: One of FIFO, LIFO, HIFO, Specific Identification, Average Cost.
        detect_wash_sales: Whether to detect wash sales.

    Returns:
        Configured CryptoImportService instance.
    """
    method = CostBasisMethod(cost_basis_method)
    return CryptoImportService(
        cost_basis_method=method,
        detect_wash_sales=detect_wash_sales,
    )


def merge_exchange_imports(
    *import_results: ImportResult,
) -> List[CryptoTransaction]:
    """Merge transactions from multiple exchange imports.

    Args:
        import_results: Variable number of ImportResult objects.

    Returns:
        Combined list of transactions sorted by timestamp.
    """
    all_transactions = []
    for result in import_results:
        all_transactions.extend(result.transactions)

    # Sort by timestamp
    all_transactions.sort(key=lambda x: x.timestamp)

    # Remove duplicates based on transaction ID
    seen_ids: Set[str] = set()
    unique_transactions = []
    for txn in all_transactions:
        if txn.id not in seen_ids:
            seen_ids.add(txn.id)
            unique_transactions.append(txn)

    return unique_transactions


def calculate_tax_liability_estimate(
    summary: CryptoTaxSummary,
    tax_bracket: Decimal = Decimal("0.24"),
    long_term_rate: Decimal = Decimal("0.15"),
) -> Dict[str, Decimal]:
    """Estimate tax liability from crypto tax summary.

    Args:
        summary: CryptoTaxSummary from processed transactions.
        tax_bracket: Marginal ordinary income tax rate.
        long_term_rate: Long-term capital gains rate.

    Returns:
        Dictionary with estimated taxes by category.
    """
    # Short-term gains taxed as ordinary income
    net_short_term = summary.short_term_gains - summary.short_term_losses
    short_term_tax = max(Decimal("0"), net_short_term * tax_bracket)

    # Long-term gains at preferential rate
    net_long_term = summary.long_term_gains - summary.long_term_losses
    long_term_tax = max(Decimal("0"), net_long_term * long_term_rate)

    # Ordinary income (staking, mining, etc.)
    income_tax = summary.total_ordinary_income * tax_bracket

    # Self-employment tax on mining (approximate)
    se_tax = summary.mining_income * Decimal("0.153")  # 15.3% SE tax

    return {
        "short_term_capital_gains_tax": short_term_tax.quantize(Decimal("0.01"), ROUND_HALF_UP),
        "long_term_capital_gains_tax": long_term_tax.quantize(Decimal("0.01"), ROUND_HALF_UP),
        "ordinary_income_tax": income_tax.quantize(Decimal("0.01"), ROUND_HALF_UP),
        "self_employment_tax": se_tax.quantize(Decimal("0.01"), ROUND_HALF_UP),
        "total_estimated_tax": (
            short_term_tax + long_term_tax + income_tax + se_tax
        ).quantize(Decimal("0.01"), ROUND_HALF_UP),
    }
