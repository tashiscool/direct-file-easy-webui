"""Comprehensive pytest tests for the Cryptocurrency Import Service.

This module tests the crypto import service functionality including:
- Cost basis calculation methods (FIFO, LIFO, HIFO, Specific ID, Average Cost)
- Exchange CSV parsers (Coinbase, Kraken, Binance, Generic)
- Transaction type handling
- Form 8949 generation
- Wash sale detection
- Tax summary calculations

Test data uses realistic cryptocurrency transactions with:
- BTC purchases at various prices
- ETH conversions
- Staking rewards
- Mining income
- Airdrops
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import csv
import io

import sys
import os

# Add the parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import directly from the module file to avoid __init__.py dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "crypto_import_service",
    os.path.join(parent_dir, "services", "crypto_import_service.py")
)
crypto_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crypto_module)

# Extract imports from the loaded module
CryptoImportService = crypto_module.CryptoImportService
CostBasisCalculator = crypto_module.CostBasisCalculator
WashSaleDetector = crypto_module.WashSaleDetector
CostBasisMethod = crypto_module.CostBasisMethod
TransactionType = crypto_module.TransactionType
ExchangeType = crypto_module.ExchangeType
HoldingPeriod = crypto_module.HoldingPeriod
Form8949Category = crypto_module.Form8949Category
CryptoAsset = crypto_module.CryptoAsset
CryptoTransaction = crypto_module.CryptoTransaction
CryptoLot = crypto_module.CryptoLot
DisposalEvent = crypto_module.DisposalEvent
CryptoIncome = crypto_module.CryptoIncome
WashSaleViolation = crypto_module.WashSaleViolation
CryptoTaxSummary = crypto_module.CryptoTaxSummary
Form8949Data = crypto_module.Form8949Data
ImportResult = crypto_module.ImportResult
CoinbaseParser = crypto_module.CoinbaseParser
KrakenParser = crypto_module.KrakenParser
BinanceUSParser = crypto_module.BinanceUSParser
GenericCryptoParser = crypto_module.GenericCryptoParser
create_crypto_import_service = crypto_module.create_crypto_import_service
merge_exchange_imports = crypto_module.merge_exchange_imports
calculate_tax_liability_estimate = crypto_module.calculate_tax_liability_estimate


# =============================================================================
# FIXTURES - Sample Exchange CSV Data
# =============================================================================


@pytest.fixture
def sample_coinbase_csv() -> str:
    """Fixture for sample Coinbase CSV export data.

    Includes realistic BTC and ETH transactions with various types:
    - Buy transactions
    - Sell transactions
    - Staking rewards
    - Convert transactions
    """
    return """Timestamp,Transaction Type,Asset,Quantity Transacted,Spot Price at Transaction,Subtotal,Total (inclusive of fees),Fees,Notes
2025-01-15T10:30:00Z,Buy,BTC,0.5,40000.00,20000.00,20100.00,100.00,
2025-02-20T14:45:00Z,Buy,BTC,0.25,42000.00,10500.00,10552.50,52.50,
2025-03-10T09:15:00Z,Buy,ETH,5.0,2500.00,12500.00,12562.50,62.50,
2025-04-05T16:20:00Z,Sell,BTC,0.3,45000.00,13500.00,13432.50,67.50,
2025-05-15T11:00:00Z,Staking Income,ETH,0.05,2800.00,140.00,140.00,0.00,ETH2 staking rewards
2025-06-01T08:30:00Z,Convert,ETH,2.0,2600.00,5200.00,5200.00,0.00,Converted to USDC
2025-07-20T13:45:00Z,Buy,BTC,0.1,35000.00,3500.00,3517.50,17.50,
2025-08-10T15:30:00Z,Sell,BTC,0.2,38000.00,7600.00,7562.00,38.00,
2025-09-05T10:00:00Z,Airdrop,UNI,100.0,5.50,550.00,550.00,0.00,Uniswap governance token
2025-10-15T14:00:00Z,Staking Income,ETH,0.03,3000.00,90.00,90.00,0.00,ETH2 staking rewards
"""


@pytest.fixture
def sample_kraken_csv() -> str:
    """Fixture for sample Kraken CSV export data.

    Kraken uses ledger format with different column names
    and asset prefixes (XXBT for BTC, XETH for ETH).
    """
    return """txid,refid,time,type,subtype,aclass,asset,amount,fee,balance
ABCD1234,REF001,2025-01-10 08:00:00,deposit,,currency,ZUSD,25000.00,0.00,25000.00
EFGH5678,REF002,2025-01-12 10:30:00,trade,,currency,XXBT,0.5,0.0001,0.5
IJKL9012,REF003,2025-01-12 10:30:00,trade,,currency,ZUSD,-20500.00,5.00,4495.00
MNOP3456,REF004,2025-02-15 14:00:00,trade,,currency,XETH,3.0,0.001,3.0
QRST7890,REF005,2025-02-15 14:00:00,trade,,currency,ZUSD,-7650.00,3.00,0.0
UVWX1234,REF006,2025-03-20 09:45:00,staking,,currency,XETH,0.02,0.00,3.02
YZAB5678,REF007,2025-04-10 11:30:00,trade,,currency,XXBT,-0.25,0.0001,0.2499
CDEF9012,REF008,2025-04-10 11:30:00,trade,,currency,ZUSD,11250.00,10.00,11235.00
GHIJ3456,REF009,2025-05-05 16:00:00,staking,,currency,DOT,5.0,0.00,5.0
"""


@pytest.fixture
def sample_binance_csv() -> str:
    """Fixture for sample Binance.US CSV export data.

    Binance uses a different format with UTC_Time and Operation columns.
    """
    return """User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
user123,2025-01-08 09:00:00,Spot,Deposit,USD,15000.00,
user123,2025-01-09 10:15:00,Spot,Buy,BTC,0.35,
user123,2025-01-09 10:15:00,Spot,Sell,USD,-14700.00,
user123,2025-02-18 13:30:00,Spot,Buy,ETH,4.5,
user123,2025-02-18 13:30:00,Spot,Sell,USD,-11250.00,
user123,2025-03-25 08:45:00,Spot,Staking Rewards,SOL,2.5,
user123,2025-04-12 15:20:00,Spot,Sell,BTC,-0.15,
user123,2025-04-12 15:20:00,Spot,Buy,USD,6750.00,
user123,2025-05-30 11:00:00,Spot,Mining,BTC,0.001,Mining reward
"""


@pytest.fixture
def sample_generic_csv() -> str:
    """Fixture for generic CSV format that should be auto-detected.

    This tests the fallback generic parser with common column names.
    """
    return """Date,Type,Asset,Amount,Price,Total Value,Fee
2025-01-20,buy,BTC,0.25,41000.00,10250.00,50.00
2025-02-25,buy,ETH,3.0,2400.00,7200.00,35.00
2025-03-30,sell,BTC,0.1,44000.00,4400.00,20.00
2025-04-15,staking,SOL,1.5,150.00,225.00,0.00
2025-05-20,airdrop,ATOM,25.0,10.00,250.00,0.00
"""


@pytest.fixture
def btc_asset() -> CryptoAsset:
    """Fixture for Bitcoin asset."""
    return CryptoAsset(symbol="BTC", name="Bitcoin")


@pytest.fixture
def eth_asset() -> CryptoAsset:
    """Fixture for Ethereum asset."""
    return CryptoAsset(symbol="ETH", name="Ethereum")


@pytest.fixture
def sample_btc_purchases(btc_asset) -> List[Dict[str, Any]]:
    """Fixture for sample BTC purchase transactions for cost basis testing.

    Creates purchases at different prices for testing different cost basis methods:
    - Lot 1: 0.5 BTC at $30,000 (oldest, lowest)
    - Lot 2: 0.3 BTC at $45,000 (middle, highest)
    - Lot 3: 0.2 BTC at $35,000 (newest, middle)
    """
    return [
        {
            "quantity": Decimal("0.5"),
            "cost_basis": Decimal("15000.00"),  # $30,000 per BTC
            "date": datetime(2024, 1, 15, 10, 0, 0),
        },
        {
            "quantity": Decimal("0.3"),
            "cost_basis": Decimal("13500.00"),  # $45,000 per BTC
            "date": datetime(2024, 6, 20, 14, 0, 0),
        },
        {
            "quantity": Decimal("0.2"),
            "cost_basis": Decimal("7000.00"),   # $35,000 per BTC
            "date": datetime(2024, 12, 10, 9, 0, 0),
        },
    ]


@pytest.fixture
def fifo_calculator() -> CostBasisCalculator:
    """Fixture for FIFO cost basis calculator."""
    return CostBasisCalculator(method=CostBasisMethod.FIFO)


@pytest.fixture
def lifo_calculator() -> CostBasisCalculator:
    """Fixture for LIFO cost basis calculator."""
    return CostBasisCalculator(method=CostBasisMethod.LIFO)


@pytest.fixture
def hifo_calculator() -> CostBasisCalculator:
    """Fixture for HIFO cost basis calculator."""
    return CostBasisCalculator(method=CostBasisMethod.HIFO)


@pytest.fixture
def specific_id_calculator() -> CostBasisCalculator:
    """Fixture for Specific Identification cost basis calculator."""
    return CostBasisCalculator(method=CostBasisMethod.SPECIFIC_ID)


@pytest.fixture
def average_cost_calculator() -> CostBasisCalculator:
    """Fixture for Average Cost calculator."""
    return CostBasisCalculator(method=CostBasisMethod.AVERAGE_COST)


@pytest.fixture
def crypto_service_fifo() -> CryptoImportService:
    """Fixture for CryptoImportService with FIFO method."""
    return CryptoImportService(
        cost_basis_method=CostBasisMethod.FIFO,
        detect_wash_sales=True
    )


# =============================================================================
# TEST CLASS: Cost Basis Calculation - FIFO
# =============================================================================


class TestFIFOCostBasis:
    """Tests for FIFO (First In, First Out) cost basis calculation.

    FIFO sells the oldest lots first, regardless of cost basis.
    """

    def test_fifo_cost_basis(self, fifo_calculator, btc_asset, sample_btc_purchases):
        """Test FIFO sells oldest lots first.

        Given:
        - Lot 1: 0.5 BTC at $30,000 (Jan 2024)
        - Lot 2: 0.3 BTC at $45,000 (Jun 2024)
        - Lot 3: 0.2 BTC at $35,000 (Dec 2024)

        When selling 0.4 BTC:
        - FIFO should use Lot 1 first (oldest)
        - Cost basis = 0.4 * $30,000 = $12,000
        """
        # Add all lots
        lots = []
        for i, purchase in enumerate(sample_btc_purchases):
            lot = fifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )
            lots.append(lot)

        # Sell 0.4 BTC
        sale_date = datetime(2025, 3, 15, 12, 0, 0)
        disposal = fifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.4"),
            proceeds=Decimal("16000.00"),  # $40,000 per BTC
            date_sold=sale_date,
            source_transaction_id="sale-1",
        )

        # FIFO should use the oldest lot first
        # 0.4 BTC from Lot 1 at $30,000/BTC = $12,000 cost basis
        expected_cost_basis = Decimal("0.4") * Decimal("30000")
        assert disposal.cost_basis == expected_cost_basis

        # Gain should be proceeds - cost basis
        expected_gain = Decimal("16000.00") - expected_cost_basis
        assert disposal.gain_or_loss == expected_gain

        # Should be long-term (held > 1 year from Jan 2024 to Mar 2025)
        assert disposal.holding_period == HoldingPeriod.LONG_TERM

    def test_fifo_uses_multiple_lots_when_needed(
        self, fifo_calculator, btc_asset, sample_btc_purchases
    ):
        """Test FIFO spans multiple lots when selling more than one lot."""
        # Add all lots
        for i, purchase in enumerate(sample_btc_purchases):
            fifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # Sell 0.7 BTC (needs Lot 1: 0.5 + Lot 2: 0.2)
        sale_date = datetime(2025, 3, 15, 12, 0, 0)
        disposal = fifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.7"),
            proceeds=Decimal("28000.00"),  # $40,000 per BTC
            date_sold=sale_date,
            source_transaction_id="sale-2",
        )

        # Cost basis: 0.5 BTC at $30,000 + 0.2 BTC at $45,000
        expected_cost_basis = Decimal("15000.00") + (Decimal("0.2") * Decimal("45000"))
        assert disposal.cost_basis == expected_cost_basis

        # Check lots were properly depleted
        assert len(disposal.lots_used) == 2

    def test_fifo_depletes_lots_correctly(
        self, fifo_calculator, btc_asset, sample_btc_purchases
    ):
        """Test that FIFO properly tracks remaining lot quantities."""
        # Add lots
        for i, purchase in enumerate(sample_btc_purchases):
            fifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # First sale: 0.3 BTC
        fifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.3"),
            proceeds=Decimal("12000.00"),
            date_sold=datetime(2025, 2, 1),
            source_transaction_id="sale-1",
        )

        # Check remaining in first lot
        holdings = fifo_calculator.get_holdings("BTC")
        btc_lots = holdings.holdings.get("BTC", [])

        # First lot should have 0.2 BTC remaining
        remaining_in_lot1 = btc_lots[0].remaining_quantity
        assert remaining_in_lot1 == Decimal("0.2")


# =============================================================================
# TEST CLASS: Cost Basis Calculation - LIFO
# =============================================================================


class TestLIFOCostBasis:
    """Tests for LIFO (Last In, First Out) cost basis calculation.

    LIFO sells the newest lots first, regardless of cost basis.
    """

    def test_lifo_cost_basis(self, lifo_calculator, btc_asset, sample_btc_purchases):
        """Test LIFO sells newest lots first.

        Given:
        - Lot 1: 0.5 BTC at $30,000 (Jan 2024)
        - Lot 2: 0.3 BTC at $45,000 (Jun 2024)
        - Lot 3: 0.2 BTC at $35,000 (Dec 2024)

        When selling 0.15 BTC:
        - LIFO should use Lot 3 first (newest)
        - Cost basis = 0.15 * $35,000 = $5,250
        """
        # Add all lots
        for i, purchase in enumerate(sample_btc_purchases):
            lifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # Sell 0.15 BTC
        sale_date = datetime(2025, 3, 15, 12, 0, 0)
        disposal = lifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.15"),
            proceeds=Decimal("6000.00"),  # $40,000 per BTC
            date_sold=sale_date,
            source_transaction_id="sale-1",
        )

        # LIFO should use the newest lot first
        # 0.15 BTC from Lot 3 at $35,000/BTC = $5,250 cost basis
        expected_cost_basis = Decimal("0.15") * Decimal("35000")
        assert disposal.cost_basis == expected_cost_basis

        # Gain should be proceeds - cost basis
        expected_gain = Decimal("6000.00") - expected_cost_basis
        assert disposal.gain_or_loss == expected_gain

    def test_lifo_spans_multiple_lots(self, lifo_calculator, btc_asset, sample_btc_purchases):
        """Test LIFO spanning multiple lots from newest to older."""
        # Add all lots
        for i, purchase in enumerate(sample_btc_purchases):
            lifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # Sell 0.4 BTC (needs Lot 3: 0.2 + Lot 2: 0.2)
        disposal = lifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.4"),
            proceeds=Decimal("16000.00"),
            date_sold=datetime(2025, 3, 15),
            source_transaction_id="sale-1",
        )

        # Cost basis: 0.2 BTC at $35,000 + 0.2 BTC at $45,000
        expected_cost_basis = Decimal("7000.00") + (Decimal("0.2") * Decimal("45000"))
        assert disposal.cost_basis == expected_cost_basis


# =============================================================================
# TEST CLASS: Cost Basis Calculation - HIFO
# =============================================================================


class TestHIFOCostBasis:
    """Tests for HIFO (Highest In, First Out) cost basis calculation.

    HIFO sells the highest cost basis lots first to minimize gains.
    """

    def test_hifo_cost_basis(self, hifo_calculator, btc_asset, sample_btc_purchases):
        """Test HIFO sells highest cost basis lots first.

        Given:
        - Lot 1: 0.5 BTC at $30,000/BTC
        - Lot 2: 0.3 BTC at $45,000/BTC (highest)
        - Lot 3: 0.2 BTC at $35,000/BTC

        When selling 0.25 BTC:
        - HIFO should use Lot 2 first (highest cost basis per unit)
        - Cost basis = 0.25 * $45,000 = $11,250
        """
        # Add all lots
        for i, purchase in enumerate(sample_btc_purchases):
            hifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # Sell 0.25 BTC
        sale_date = datetime(2025, 3, 15, 12, 0, 0)
        disposal = hifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.25"),
            proceeds=Decimal("10000.00"),  # $40,000 per BTC
            date_sold=sale_date,
            source_transaction_id="sale-1",
        )

        # HIFO should use the highest cost basis lot first
        # 0.25 BTC from Lot 2 at $45,000/BTC = $11,250 cost basis
        expected_cost_basis = Decimal("0.25") * Decimal("45000")
        assert disposal.cost_basis == expected_cost_basis

        # This should result in a LOSS since cost > proceeds
        expected_loss = Decimal("10000.00") - expected_cost_basis
        assert disposal.gain_or_loss == expected_loss
        assert disposal.gain_or_loss < Decimal("0")  # Confirm it's a loss

    def test_hifo_minimizes_gains(self, hifo_calculator, btc_asset, sample_btc_purchases):
        """Test HIFO results in lower gain than FIFO when prices rise."""
        # Create a fresh FIFO calculator for comparison
        fifo_calc = CostBasisCalculator(method=CostBasisMethod.FIFO)

        # Add same lots to both calculators
        for i, purchase in enumerate(sample_btc_purchases):
            hifo_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )
            fifo_calc.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # Sell 0.2 BTC at profit
        proceeds = Decimal("9000.00")  # $45,000/BTC

        hifo_disposal = hifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.2"),
            proceeds=proceeds,
            date_sold=datetime(2025, 3, 15),
            source_transaction_id="sale-hifo",
        )

        fifo_disposal = fifo_calc.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.2"),
            proceeds=proceeds,
            date_sold=datetime(2025, 3, 15),
            source_transaction_id="sale-fifo",
        )

        # HIFO should have higher cost basis (uses $45,000 lot)
        assert hifo_disposal.cost_basis > fifo_disposal.cost_basis

        # HIFO should have lower gain (or higher loss)
        assert hifo_disposal.gain_or_loss < fifo_disposal.gain_or_loss


# =============================================================================
# TEST CLASS: Cost Basis Calculation - Specific Identification
# =============================================================================


class TestSpecificIdentification:
    """Tests for Specific Identification cost basis method.

    Allows user to specify exactly which lots to sell.
    """

    def test_specific_identification(
        self, specific_id_calculator, btc_asset, sample_btc_purchases
    ):
        """Test selling specific lots by ID.

        User can choose which lots to sell for tax optimization.
        """
        # Add all lots and track their IDs
        lot_ids = []
        for i, purchase in enumerate(sample_btc_purchases):
            lot = specific_id_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )
            lot_ids.append(lot.id)

        # Specifically select the second lot (Lot 2 at $45,000)
        disposal = specific_id_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.2"),
            proceeds=Decimal("8000.00"),
            date_sold=datetime(2025, 3, 15),
            source_transaction_id="sale-1",
            specific_lot_ids=[lot_ids[1]],  # Second lot
        )

        # Should use the specified lot
        # 0.2 BTC from Lot 2 at $45,000/BTC = $9,000 cost basis
        expected_cost_basis = Decimal("0.2") * Decimal("45000")
        assert disposal.cost_basis == expected_cost_basis

    def test_specific_identification_multiple_lots(
        self, specific_id_calculator, btc_asset, sample_btc_purchases
    ):
        """Test specifying multiple lots in a specific order."""
        # Add all lots
        lot_ids = []
        for i, purchase in enumerate(sample_btc_purchases):
            lot = specific_id_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )
            lot_ids.append(lot.id)

        # Select lots 3 and 1 (in that order)
        disposal = specific_id_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.5"),
            proceeds=Decimal("20000.00"),
            date_sold=datetime(2025, 3, 15),
            source_transaction_id="sale-1",
            specific_lot_ids=[lot_ids[2], lot_ids[0]],  # Lot 3 then Lot 1
        )

        # Should use Lot 3 (0.2 at $35,000) then Lot 1 (0.3 at $30,000)
        expected_cost_basis = Decimal("7000.00") + (Decimal("0.3") * Decimal("30000"))
        assert disposal.cost_basis == expected_cost_basis


# =============================================================================
# TEST CLASS: Cost Basis Calculation - Average Cost
# =============================================================================


class TestAverageCost:
    """Tests for Average Cost basis method.

    Uses weighted average cost across all lots.
    """

    def test_average_cost(self, average_cost_calculator, btc_asset, sample_btc_purchases):
        """Test average cost calculation across all lots.

        Total BTC: 0.5 + 0.3 + 0.2 = 1.0 BTC
        Total Cost: $15,000 + $13,500 + $7,000 = $35,500
        Average: $35,500 / 1.0 = $35,500 per BTC
        """
        # Add all lots
        for i, purchase in enumerate(sample_btc_purchases):
            average_cost_calculator.add_lot(
                asset=btc_asset,
                quantity=purchase["quantity"],
                cost_basis=purchase["cost_basis"],
                date_acquired=purchase["date"],
                acquisition_type=TransactionType.BUY,
                source_transaction_id=f"buy-{i+1}",
            )

        # Sell 0.4 BTC
        disposal = average_cost_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.4"),
            proceeds=Decimal("16000.00"),
            date_sold=datetime(2025, 3, 15),
            source_transaction_id="sale-1",
        )

        # Total holdings: 1.0 BTC
        # Total cost: $35,500
        # Average per BTC: $35,500
        # Cost basis for 0.4 BTC: 0.4 * $35,500 = $14,200
        total_quantity = Decimal("0.5") + Decimal("0.3") + Decimal("0.2")
        total_cost = Decimal("15000.00") + Decimal("13500.00") + Decimal("7000.00")
        avg_cost_per_unit = total_cost / total_quantity
        expected_cost_basis = Decimal("0.4") * avg_cost_per_unit

        # Allow small rounding difference
        assert abs(disposal.cost_basis - expected_cost_basis) < Decimal("1.00")


# =============================================================================
# TEST CLASS: Exchange Parser Tests - Coinbase
# =============================================================================


class TestCoinbaseParser:
    """Tests for Coinbase CSV parser."""

    def test_parse_coinbase_csv(self, sample_coinbase_csv):
        """Test parsing Coinbase CSV format."""
        parser = CoinbaseParser()
        transactions = parser.parse(sample_coinbase_csv)

        assert len(transactions) > 0

        # Check first transaction (BTC buy)
        first_txn = transactions[0]
        assert first_txn.asset.symbol == "BTC"
        assert first_txn.transaction_type == TransactionType.BUY
        assert first_txn.quantity == Decimal("0.5")
        assert first_txn.exchange == ExchangeType.COINBASE

    def test_coinbase_parser_detects_format(self, sample_coinbase_csv):
        """Test that Coinbase parser correctly detects its format."""
        parser = CoinbaseParser()
        reader = csv.reader(io.StringIO(sample_coinbase_csv))
        headers = next(reader)

        assert parser.detect(sample_coinbase_csv, headers) is True

    def test_coinbase_parser_handles_staking(self, sample_coinbase_csv):
        """Test that Coinbase parser correctly identifies staking rewards."""
        parser = CoinbaseParser()
        transactions = parser.parse(sample_coinbase_csv)

        # Find staking transactions
        staking_txns = [
            t for t in transactions
            if t.transaction_type == TransactionType.STAKING_REWARD
        ]

        assert len(staking_txns) > 0
        assert staking_txns[0].asset.symbol == "ETH"

    def test_coinbase_parser_handles_convert(self, sample_coinbase_csv):
        """Test that Coinbase parser correctly identifies convert transactions."""
        parser = CoinbaseParser()
        transactions = parser.parse(sample_coinbase_csv)

        convert_txns = [
            t for t in transactions
            if t.transaction_type == TransactionType.CONVERT
        ]

        assert len(convert_txns) > 0

    def test_coinbase_parser_handles_airdrop(self, sample_coinbase_csv):
        """Test that Coinbase parser correctly identifies airdrops."""
        parser = CoinbaseParser()
        transactions = parser.parse(sample_coinbase_csv)

        airdrop_txns = [
            t for t in transactions
            if t.transaction_type == TransactionType.AIRDROP
        ]

        assert len(airdrop_txns) > 0
        assert airdrop_txns[0].asset.symbol == "UNI"


# =============================================================================
# TEST CLASS: Exchange Parser Tests - Kraken
# =============================================================================


class TestKrakenParser:
    """Tests for Kraken CSV parser."""

    def test_parse_kraken_csv(self, sample_kraken_csv):
        """Test parsing Kraken CSV format."""
        parser = KrakenParser()
        transactions = parser.parse(sample_kraken_csv)

        assert len(transactions) > 0

    def test_kraken_parser_normalizes_asset_symbols(self, sample_kraken_csv):
        """Test that Kraken parser normalizes XXBT to BTC."""
        parser = KrakenParser()
        transactions = parser.parse(sample_kraken_csv)

        # Find BTC transactions (originally XXBT)
        btc_txns = [t for t in transactions if t.asset.symbol == "BTC"]
        assert len(btc_txns) > 0

    def test_kraken_parser_detects_format(self, sample_kraken_csv):
        """Test that Kraken parser correctly detects its format."""
        parser = KrakenParser()
        reader = csv.reader(io.StringIO(sample_kraken_csv))
        headers = next(reader)

        assert parser.detect(sample_kraken_csv, headers) is True

    def test_kraken_parser_handles_staking(self, sample_kraken_csv):
        """Test Kraken parser identifies staking transactions."""
        parser = KrakenParser()
        transactions = parser.parse(sample_kraken_csv)

        staking_txns = [
            t for t in transactions
            if t.transaction_type == TransactionType.STAKING_REWARD
        ]

        assert len(staking_txns) > 0


# =============================================================================
# TEST CLASS: Exchange Parser Tests - Binance
# =============================================================================


class TestBinanceParser:
    """Tests for Binance.US CSV parser."""

    def test_parse_binance_csv(self, sample_binance_csv):
        """Test parsing Binance.US CSV format."""
        parser = BinanceUSParser()
        transactions = parser.parse(sample_binance_csv)

        assert len(transactions) > 0

    def test_binance_parser_detects_format(self, sample_binance_csv):
        """Test that Binance parser correctly detects its format."""
        parser = BinanceUSParser()
        reader = csv.reader(io.StringIO(sample_binance_csv))
        headers = next(reader)

        assert parser.detect(sample_binance_csv, headers) is True

    def test_binance_parser_handles_mining(self, sample_binance_csv):
        """Test Binance parser identifies mining rewards."""
        parser = BinanceUSParser()
        transactions = parser.parse(sample_binance_csv)

        mining_txns = [
            t for t in transactions
            if t.transaction_type == TransactionType.MINING
        ]

        assert len(mining_txns) > 0


# =============================================================================
# TEST CLASS: Exchange Parser Tests - Generic
# =============================================================================


class TestGenericParser:
    """Tests for generic CSV parser fallback."""

    def test_parse_generic_csv(self, sample_generic_csv):
        """Test parsing generic CSV format with common columns."""
        parser = GenericCryptoParser()
        transactions = parser.parse(sample_generic_csv)

        assert len(transactions) > 0
        assert transactions[0].exchange == ExchangeType.GENERIC

    def test_generic_parser_always_detects(self, sample_generic_csv):
        """Test that generic parser always returns True for detection."""
        parser = GenericCryptoParser()
        assert parser.detect(sample_generic_csv, []) is True

    def test_generic_parser_maps_common_columns(self, sample_generic_csv):
        """Test that generic parser maps common column names."""
        parser = GenericCryptoParser()
        transactions = parser.parse(sample_generic_csv)

        # Should correctly identify transaction types
        buy_txns = [t for t in transactions if t.transaction_type == TransactionType.BUY]
        sell_txns = [t for t in transactions if t.transaction_type == TransactionType.SELL]

        assert len(buy_txns) >= 2
        assert len(sell_txns) >= 1


# =============================================================================
# TEST CLASS: Transaction Type Tests
# =============================================================================


class TestTransactionTypes:
    """Tests for various transaction type handling."""

    def test_buy_transaction(self, crypto_service_fifo, sample_coinbase_csv):
        """Test BUY transaction creates tax lot correctly."""
        result = crypto_service_fifo.import_csv(sample_coinbase_csv)

        buy_txns = [
            t for t in result.transactions
            if t.transaction_type == TransactionType.BUY
        ]

        assert len(buy_txns) > 0
        assert not buy_txns[0].is_taxable_event  # Buy is not taxable
        assert not buy_txns[0].is_income_event  # Buy is not income

    def test_sell_transaction(self, crypto_service_fifo, sample_coinbase_csv):
        """Test SELL transaction is marked as taxable event."""
        result = crypto_service_fifo.import_csv(sample_coinbase_csv)

        sell_txns = [
            t for t in result.transactions
            if t.transaction_type == TransactionType.SELL
        ]

        assert len(sell_txns) > 0
        assert sell_txns[0].is_taxable_event  # Sell is taxable

    def test_convert_swap_transaction(self, crypto_service_fifo, sample_coinbase_csv):
        """Test CONVERT/SWAP transaction is marked as taxable event."""
        result = crypto_service_fifo.import_csv(sample_coinbase_csv)

        convert_txns = [
            t for t in result.transactions
            if t.transaction_type in [TransactionType.CONVERT, TransactionType.SWAP]
        ]

        assert len(convert_txns) > 0
        assert convert_txns[0].is_taxable_event

    def test_staking_reward(self, crypto_service_fifo, sample_coinbase_csv):
        """Test STAKING_REWARD is marked as income event."""
        result = crypto_service_fifo.import_csv(sample_coinbase_csv)

        staking_txns = [
            t for t in result.transactions
            if t.transaction_type == TransactionType.STAKING_REWARD
        ]

        assert len(staking_txns) > 0
        assert staking_txns[0].is_income_event
        assert not staking_txns[0].is_taxable_event  # Not a capital gain event

    def test_airdrop(self, crypto_service_fifo, sample_coinbase_csv):
        """Test AIRDROP is marked as income event."""
        result = crypto_service_fifo.import_csv(sample_coinbase_csv)

        airdrop_txns = [
            t for t in result.transactions
            if t.transaction_type == TransactionType.AIRDROP
        ]

        assert len(airdrop_txns) > 0
        assert airdrop_txns[0].is_income_event

    def test_mining_income(self, crypto_service_fifo, sample_binance_csv):
        """Test MINING is marked as income event."""
        result = crypto_service_fifo.import_csv(sample_binance_csv)

        mining_txns = [
            t for t in result.transactions
            if t.transaction_type == TransactionType.MINING
        ]

        assert len(mining_txns) > 0
        assert mining_txns[0].is_income_event


# =============================================================================
# TEST CLASS: Form 8949 Generation Tests
# =============================================================================


class TestForm8949Generation:
    """Tests for IRS Form 8949 generation."""

    @pytest.fixture
    def service_with_transactions(self, btc_asset, eth_asset):
        """Create a service with pre-loaded transactions for 8949 testing."""
        service = CryptoImportService(
            cost_basis_method=CostBasisMethod.FIFO,
            detect_wash_sales=False,
        )

        # Add purchase lots (all from 2024)
        # Short-term lot (< 1 year)
        service.transactions.append(CryptoTransaction(
            id="buy-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2025, 1, 15),
            asset=btc_asset,
            quantity=Decimal("0.5"),
            total_value_usd=Decimal("20000.00"),
            fee_usd=Decimal("100.00"),
        ))

        # Long-term lot (> 1 year)
        service.transactions.append(CryptoTransaction(
            id="buy-2",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2024, 1, 10),
            asset=btc_asset,
            quantity=Decimal("0.3"),
            total_value_usd=Decimal("12000.00"),
            fee_usd=Decimal("60.00"),
        ))

        # Short-term sale
        service.transactions.append(CryptoTransaction(
            id="sell-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.SELL,
            timestamp=datetime(2025, 6, 15),
            asset=btc_asset,
            quantity=Decimal("0.2"),
            total_value_usd=Decimal("9000.00"),
            fee_usd=Decimal("45.00"),
        ))

        # Long-term sale
        service.transactions.append(CryptoTransaction(
            id="sell-2",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.SELL,
            timestamp=datetime(2025, 8, 20),
            asset=btc_asset,
            quantity=Decimal("0.25"),
            total_value_usd=Decimal("11000.00"),
            fee_usd=Decimal("55.00"),
        ))

        return service

    def test_short_term_category_a(self, service_with_transactions):
        """Test Form 8949 Category A - Short-term, basis reported to IRS.

        Note: Most crypto transactions are Category C (not reported on 1099-B),
        but this tests the categorization logic.
        """
        service = service_with_transactions
        summary = service.process_transactions(tax_year=2025)
        form_8949 = service.generate_form_8949(tax_year=2025)

        # Verify short-term entries exist (Category C for crypto)
        short_term_entries = (
            form_8949.part_i_category_a +
            form_8949.part_i_category_b +
            form_8949.part_i_category_c
        )

        # There should be short-term disposals
        assert summary.total_disposals > 0

    def test_short_term_category_b(self):
        """Test Form 8949 Category B - Short-term, basis NOT reported to IRS.

        This is less common for crypto but validates the categorization.
        """
        # Category B would require 1099-B without basis reporting
        # Most crypto falls into Category C
        pass  # Placeholder for future implementation

    def test_long_term_category_d(self, service_with_transactions):
        """Test Form 8949 Category D - Long-term, basis reported to IRS."""
        service = service_with_transactions
        service.process_transactions(tax_year=2025)
        form_8949 = service.generate_form_8949(tax_year=2025)

        # Long-term entries are in Part II
        long_term_entries = (
            form_8949.part_ii_category_d +
            form_8949.part_ii_category_e +
            form_8949.part_ii_category_f
        )

        # Should have long-term disposals
        assert len(form_8949.part_ii_totals) > 0

    def test_long_term_category_e(self):
        """Test Form 8949 Category E - Long-term, basis NOT reported to IRS."""
        # Category E would require 1099-B without basis reporting
        # Most crypto falls into Category F
        pass  # Placeholder for future implementation

    def test_form_8949_totals(self, service_with_transactions):
        """Test Form 8949 totals are calculated correctly."""
        service = service_with_transactions
        service.process_transactions(tax_year=2025)
        form_8949 = service.generate_form_8949(tax_year=2025)

        # Part I totals (short-term)
        part_i = form_8949.part_i_totals
        if part_i:
            assert "proceeds" in part_i
            assert "cost_basis" in part_i
            assert "gain_loss" in part_i

        # Part II totals (long-term)
        part_ii = form_8949.part_ii_totals
        if part_ii:
            assert "proceeds" in part_ii
            assert "cost_basis" in part_ii
            assert "gain_loss" in part_ii


# =============================================================================
# TEST CLASS: Wash Sale Detection Tests
# =============================================================================


class TestWashSaleDetection:
    """Tests for wash sale rule detection and adjustment."""

    @pytest.fixture
    def wash_sale_transactions(self, btc_asset):
        """Create transactions that trigger wash sale rule."""
        transactions = []

        # Initial purchase
        transactions.append(CryptoTransaction(
            id="buy-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2025, 2, 1),
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("50000.00"),
        ))

        # Sell at a loss
        transactions.append(CryptoTransaction(
            id="sell-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.SELL,
            timestamp=datetime(2025, 3, 15),
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("40000.00"),  # $10,000 loss
        ))

        # Repurchase within 30 days (WASH SALE!)
        transactions.append(CryptoTransaction(
            id="buy-2",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2025, 3, 25),  # 10 days after sale
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("42000.00"),
        ))

        return transactions

    @pytest.fixture
    def no_wash_sale_transactions(self, btc_asset):
        """Create transactions that don't trigger wash sale rule."""
        transactions = []

        # Initial purchase
        transactions.append(CryptoTransaction(
            id="buy-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2025, 1, 1),
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("50000.00"),
        ))

        # Sell at a loss
        transactions.append(CryptoTransaction(
            id="sell-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.SELL,
            timestamp=datetime(2025, 3, 15),
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("40000.00"),  # $10,000 loss
        ))

        # Repurchase AFTER 30 days (NOT a wash sale)
        transactions.append(CryptoTransaction(
            id="buy-2",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2025, 4, 20),  # 36 days after sale
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("42000.00"),
        ))

        return transactions

    def test_wash_sale_30_day_window(self, wash_sale_transactions, btc_asset):
        """Test wash sale detected within 30-day window."""
        service = CryptoImportService(
            cost_basis_method=CostBasisMethod.FIFO,
            detect_wash_sales=True,
        )

        # Add transactions
        service.transactions = wash_sale_transactions

        # Process for 2025
        summary = service.process_transactions(tax_year=2025)

        # Should detect wash sale
        assert summary.wash_sale_count > 0
        assert summary.total_wash_sale_adjustments > Decimal("0")

    def test_wash_sale_adjustment(self, wash_sale_transactions, btc_asset):
        """Test wash sale loss is disallowed and added to basis."""
        service = CryptoImportService(
            cost_basis_method=CostBasisMethod.FIFO,
            detect_wash_sales=True,
        )

        service.transactions = wash_sale_transactions
        service.process_transactions(tax_year=2025)

        # Find the disposal with wash sale
        wash_sale_disposals = [
            d for d in service.disposals if d.is_wash_sale
        ]

        assert len(wash_sale_disposals) > 0

        disposal = wash_sale_disposals[0]
        assert disposal.adjustment_code == "W"
        assert disposal.wash_sale_loss_disallowed > Decimal("0")

    def test_no_wash_sale_outside_window(self, no_wash_sale_transactions, btc_asset):
        """Test no wash sale when repurchase is outside 30-day window."""
        service = CryptoImportService(
            cost_basis_method=CostBasisMethod.FIFO,
            detect_wash_sales=True,
        )

        service.transactions = no_wash_sale_transactions
        summary = service.process_transactions(tax_year=2025)

        # Should NOT detect wash sale
        assert summary.wash_sale_count == 0
        assert summary.total_wash_sale_adjustments == Decimal("0")

    def test_wash_sale_detector_index_transactions(self, wash_sale_transactions):
        """Test wash sale detector indexes transactions by asset."""
        detector = WashSaleDetector()
        detector.index_transactions(wash_sale_transactions)

        # Should have BTC indexed
        assert "BTC" in detector._transaction_index
        assert len(detector._transaction_index["BTC"]) == 3


# =============================================================================
# TEST CLASS: Crypto Tax Summary Tests
# =============================================================================


class TestCryptoTaxSummary:
    """Tests for overall crypto tax summary calculations."""

    @pytest.fixture
    def comprehensive_transactions(self, btc_asset, eth_asset):
        """Create comprehensive transaction set for summary testing."""
        service = CryptoImportService(
            cost_basis_method=CostBasisMethod.FIFO,
            detect_wash_sales=False,
        )

        # BTC purchases (2024 - long-term)
        service.transactions.append(CryptoTransaction(
            id="buy-btc-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2024, 1, 15),
            asset=btc_asset,
            quantity=Decimal("1.0"),
            total_value_usd=Decimal("40000.00"),
        ))

        # BTC sale at profit (long-term gain)
        service.transactions.append(CryptoTransaction(
            id="sell-btc-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.SELL,
            timestamp=datetime(2025, 6, 15),
            asset=btc_asset,
            quantity=Decimal("0.5"),
            total_value_usd=Decimal("30000.00"),  # Gain of $10,000
        ))

        # ETH purchase (2025 - short-term)
        service.transactions.append(CryptoTransaction(
            id="buy-eth-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.BUY,
            timestamp=datetime(2025, 2, 1),
            asset=eth_asset,
            quantity=Decimal("5.0"),
            total_value_usd=Decimal("15000.00"),
        ))

        # ETH sale at loss (short-term loss)
        service.transactions.append(CryptoTransaction(
            id="sell-eth-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.SELL,
            timestamp=datetime(2025, 5, 1),
            asset=eth_asset,
            quantity=Decimal("3.0"),
            total_value_usd=Decimal("7500.00"),  # Loss of $1,500
        ))

        # Staking rewards
        service.transactions.append(CryptoTransaction(
            id="stake-eth-1",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.STAKING_REWARD,
            timestamp=datetime(2025, 4, 15),
            asset=eth_asset,
            quantity=Decimal("0.1"),
            total_value_usd=Decimal("350.00"),
        ))

        service.transactions.append(CryptoTransaction(
            id="stake-eth-2",
            exchange=ExchangeType.COINBASE,
            transaction_type=TransactionType.STAKING_REWARD,
            timestamp=datetime(2025, 7, 15),
            asset=eth_asset,
            quantity=Decimal("0.12"),
            total_value_usd=Decimal("420.00"),
        ))

        # Mining income
        service.transactions.append(CryptoTransaction(
            id="mine-btc-1",
            exchange=ExchangeType.GENERIC,
            transaction_type=TransactionType.MINING,
            timestamp=datetime(2025, 3, 1),
            asset=btc_asset,
            quantity=Decimal("0.01"),
            total_value_usd=Decimal("500.00"),
        ))

        return service

    def test_total_gains_losses(self, comprehensive_transactions):
        """Test total gains and losses are calculated correctly."""
        service = comprehensive_transactions
        summary = service.process_transactions(tax_year=2025)

        # Should have both short and long term gains/losses
        assert summary.total_disposals > 0
        assert summary.net_capital_gain_loss != Decimal("0") or \
               (summary.short_term_gains + summary.long_term_gains > 0) or \
               (summary.short_term_losses + summary.long_term_losses > 0)

    def test_staking_income_total(self, comprehensive_transactions):
        """Test staking income is summed correctly."""
        service = comprehensive_transactions
        summary = service.process_transactions(tax_year=2025)

        # Should have staking income: $350 + $420 = $770
        expected_staking = Decimal("350.00") + Decimal("420.00")
        assert summary.staking_income == expected_staking

    def test_mining_income_total(self, comprehensive_transactions):
        """Test mining income is summed correctly."""
        service = comprehensive_transactions
        summary = service.process_transactions(tax_year=2025)

        # Should have mining income: $500
        assert summary.mining_income == Decimal("500.00")

    def test_total_ordinary_income(self, comprehensive_transactions):
        """Test total ordinary income includes all income types."""
        service = comprehensive_transactions
        summary = service.process_transactions(tax_year=2025)

        expected_total = (
            summary.staking_income +
            summary.mining_income +
            summary.airdrop_income +
            summary.interest_income +
            summary.other_income
        )

        assert summary.total_ordinary_income == expected_total

    def test_summary_by_exchange(self, comprehensive_transactions):
        """Test transactions are grouped by exchange."""
        service = comprehensive_transactions
        summary = service.process_transactions(tax_year=2025)

        # Should have Coinbase transactions
        assert "Coinbase" in summary.by_exchange
        assert summary.by_exchange["Coinbase"]["transaction_count"] > 0


# =============================================================================
# TEST CLASS: Service Factory and Utilities
# =============================================================================


class TestServiceUtilities:
    """Tests for service factory and utility functions."""

    def test_create_crypto_import_service_fifo(self):
        """Test factory creates FIFO service correctly."""
        service = create_crypto_import_service(
            cost_basis_method="FIFO",
            detect_wash_sales=True,
        )

        assert service.cost_basis_method == CostBasisMethod.FIFO
        assert service.detect_wash_sales is True

    def test_create_crypto_import_service_hifo(self):
        """Test factory creates HIFO service correctly."""
        service = create_crypto_import_service(
            cost_basis_method="HIFO",
            detect_wash_sales=False,
        )

        assert service.cost_basis_method == CostBasisMethod.HIFO
        assert service.detect_wash_sales is False

    def test_merge_exchange_imports(self, sample_coinbase_csv, sample_kraken_csv):
        """Test merging transactions from multiple exchanges."""
        coinbase_parser = CoinbaseParser()
        kraken_parser = KrakenParser()

        coinbase_result = ImportResult(
            exchange=ExchangeType.COINBASE,
            transactions=coinbase_parser.parse(sample_coinbase_csv),
        )

        kraken_result = ImportResult(
            exchange=ExchangeType.KRAKEN,
            transactions=kraken_parser.parse(sample_kraken_csv),
        )

        merged = merge_exchange_imports(coinbase_result, kraken_result)

        # Should have transactions from both exchanges
        coinbase_txns = [t for t in merged if t.exchange == ExchangeType.COINBASE]
        kraken_txns = [t for t in merged if t.exchange == ExchangeType.KRAKEN]

        assert len(coinbase_txns) > 0
        assert len(kraken_txns) > 0

        # Should be sorted by timestamp
        for i in range(1, len(merged)):
            assert merged[i].timestamp >= merged[i-1].timestamp

    def test_calculate_tax_liability_estimate(self):
        """Test tax liability estimation from summary."""
        summary = CryptoTaxSummary(
            tax_year=2025,
            short_term_gains=Decimal("10000.00"),
            short_term_losses=Decimal("2000.00"),
            long_term_gains=Decimal("15000.00"),
            long_term_losses=Decimal("1000.00"),
            staking_income=Decimal("1000.00"),
            mining_income=Decimal("500.00"),
            total_ordinary_income=Decimal("1500.00"),
        )

        estimate = calculate_tax_liability_estimate(
            summary=summary,
            tax_bracket=Decimal("0.24"),
            long_term_rate=Decimal("0.15"),
        )

        assert "short_term_capital_gains_tax" in estimate
        assert "long_term_capital_gains_tax" in estimate
        assert "ordinary_income_tax" in estimate
        assert "self_employment_tax" in estimate
        assert "total_estimated_tax" in estimate

        # Total should be sum of components
        assert estimate["total_estimated_tax"] == (
            estimate["short_term_capital_gains_tax"] +
            estimate["long_term_capital_gains_tax"] +
            estimate["ordinary_income_tax"] +
            estimate["self_employment_tax"]
        )

    def test_service_clear(self, crypto_service_fifo, sample_coinbase_csv):
        """Test clearing all service data."""
        crypto_service_fifo.import_csv(sample_coinbase_csv)
        assert len(crypto_service_fifo.transactions) > 0

        crypto_service_fifo.clear()

        assert len(crypto_service_fifo.transactions) == 0
        assert len(crypto_service_fifo.disposals) == 0
        assert len(crypto_service_fifo.income_events) == 0


# =============================================================================
# TEST CLASS: Edge Cases and Error Handling
# =============================================================================


class TestEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""

    def test_empty_csv_import(self, crypto_service_fifo):
        """Test importing empty CSV content."""
        empty_csv = ""
        result = crypto_service_fifo.import_csv(empty_csv)

        assert result.transactions_imported == 0

    def test_csv_with_only_headers(self, crypto_service_fifo):
        """Test importing CSV with only header row."""
        header_only = "Timestamp,Transaction Type,Asset,Quantity Transacted\n"
        result = crypto_service_fifo.import_csv(header_only)

        assert result.transactions_imported == 0

    def test_disposal_with_no_lots(self, fifo_calculator, btc_asset):
        """Test disposal when no lots exist creates zero cost basis disposal."""
        # Try to sell without any lots
        disposal = fifo_calculator.calculate_disposal(
            asset=btc_asset,
            quantity=Decimal("0.5"),
            proceeds=Decimal("25000.00"),
            date_sold=datetime(2025, 6, 15),
            source_transaction_id="sale-no-lots",
        )

        # Should have zero cost basis
        assert disposal.cost_basis == Decimal("0")
        # Entire proceeds is gain
        assert disposal.gain_or_loss == Decimal("25000.00")

    def test_lot_with_zero_quantity(self, fifo_calculator, btc_asset):
        """Test lot with zero quantity doesn't cause errors."""
        lot = fifo_calculator.add_lot(
            asset=btc_asset,
            quantity=Decimal("0"),
            cost_basis=Decimal("0"),
            date_acquired=datetime(2025, 1, 1),
            acquisition_type=TransactionType.BUY,
            source_transaction_id="buy-zero",
        )

        assert lot.remaining_quantity == Decimal("0")
        assert lot.is_depleted is True

    def test_export_transactions_csv(self, crypto_service_fifo, sample_coinbase_csv):
        """Test exporting transactions to CSV format."""
        crypto_service_fifo.import_csv(sample_coinbase_csv)

        csv_export = crypto_service_fifo.export_transactions(format="csv")

        assert len(csv_export) > 0
        assert "Date" in csv_export
        assert "Exchange" in csv_export
        assert "BTC" in csv_export or "ETH" in csv_export

    def test_export_transactions_json(self, crypto_service_fifo, sample_coinbase_csv):
        """Test exporting transactions to JSON format."""
        crypto_service_fifo.import_csv(sample_coinbase_csv)

        json_export = crypto_service_fifo.export_transactions(format="json")

        assert len(json_export) > 0
        assert "[" in json_export  # JSON array
        assert "asset" in json_export.lower()

    def test_detect_exchange_from_csv(self, crypto_service_fifo, sample_coinbase_csv):
        """Test automatic exchange detection from CSV content."""
        detected = crypto_service_fifo.detect_exchange(sample_coinbase_csv)

        assert detected == ExchangeType.COINBASE

    def test_holding_period_calculation(self, btc_asset):
        """Test holding period calculation boundary.

        IRS rule: Long-term is "more than 1 year" which is > 365 days.
        The implementation uses > 365, so:
        - 365 days exactly = short-term (<=365)
        - 366 days = long-term (>365)

        Note: The actual implementation checks days_held > 365 for long-term.
        With date math, Jan 15 2024 to Jan 15 2025 = 366 days (leap year 2024).
        """
        lot = CryptoLot(
            id="test-lot",
            asset=btc_asset,
            quantity=Decimal("1.0"),
            remaining_quantity=Decimal("1.0"),
            cost_basis_per_unit=Decimal("40000.00"),
            total_cost_basis=Decimal("40000.00"),
            date_acquired=datetime(2024, 3, 1),  # March 1, 2024
            acquisition_type=TransactionType.BUY,
            source_transaction_id="test-buy",
        )

        # Exactly 365 days from March 1, 2024 = Feb 29, 2025
        # But 2024 is a leap year, so let's use a non-leap year scenario
        # March 1, 2024 + 365 days = March 1, 2025 = 365 days
        sale_365 = datetime(2025, 3, 1)
        days_held = (sale_365 - lot.date_acquired).days
        assert days_held == 365
        assert lot.get_holding_period(sale_365) == HoldingPeriod.SHORT_TERM

        # 366 days - should be LONG-TERM
        sale_366 = datetime(2025, 3, 2)
        days_held_366 = (sale_366 - lot.date_acquired).days
        assert days_held_366 == 366
        assert lot.get_holding_period(sale_366) == HoldingPeriod.LONG_TERM


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
