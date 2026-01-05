
import pandas as pd
import pytest
from data.silver.shared.transforms import (
    TTMCalculator,
    FiscalYearCalculator,
    FiscalQuarterCalculator,
    _day_of_year,
)


def test_day_of_year():
    assert _day_of_year(1, 1) == 1
    assert _day_of_year(12, 31) == 365
    assert _day_of_year(2, 28) == 59
    with pytest.raises(ValueError):
        _day_of_year(13, 1) # Invalid month


def test_ttm_calculator():
    data = {
        "ticker": ["AAPL", "AAPL", "AAPL", "AAPL", "AAPL"],
        "end": pd.to_datetime([
            "2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31", "2024-03-31"
        ]),
        "revenue": [10, 20, 30, 40, 50],
    }
    df = pd.DataFrame(data)
    calculator = TTMCalculator()
    result = calculator.calculate(df, "revenue", ["ticker"])
    assert "ttm_revenue" in result.columns
    assert result["ttm_revenue"].iloc[3] == 100  # 10+20+30+40
    assert result["ttm_revenue"].iloc[4] == 140  # 20+30+40+50


def test_fiscal_year_calculator():
    facts_data = {
        "cik10": ["AAPL", "AAPL", "MSFT", "MSFT"],
        "end": pd.to_datetime([
            "2023-03-31", "2023-09-30", "2023-06-30", "2023-12-31"
        ]),
    }
    facts = pd.DataFrame(facts_data)
    companies_data = {
        "cik10": ["AAPL", "MSFT"],
        "fye_mmdd": ["0930", "0630"],
    }
    companies = pd.DataFrame(companies_data)
    calculator = FiscalYearCalculator()
    result = calculator.calculate(facts, companies)
    assert "fiscal_year" in result.columns
    assert result["fiscal_year"].iloc[0] == 2023  # AAPL, 2023-03-31, FYE 0930
    assert result["fiscal_year"].iloc[1] == 2023  # AAPL, 2023-09-30, FYE 0930
    assert result["fiscal_year"].iloc[2] == 2023  # MSFT, 2023-06-30, FYE 0630
    assert result["fiscal_year"].iloc[3] == 2024  # MSFT, 2023-12-31, FYE 0630

    # Edge case: within tolerance
    facts_data_tolerance = {
        "cik10": ["AAPL"],
        "end": pd.to_datetime(["2023-10-07"]),  # Within 7 days of 0930
    }
    facts_tolerance = pd.DataFrame(facts_data_tolerance)
    result_tolerance = calculator.calculate(facts_tolerance, companies)
    assert result_tolerance["fiscal_year"].iloc[0] == 2023


def test_fiscal_quarter_calculator():
    data = {
        "cik10": ["AAPL", "AAPL", "MSFT", "MSFT"],
        "end": pd.to_datetime([
            "2023-01-31", "2023-04-30", "2023-09-30", "2023-12-31"
        ]),
    }
    df = pd.DataFrame(data)
    fye_map = {"AAPL": "0930", "MSFT": "0630"}
    calculator = FiscalQuarterCalculator()
    result = calculator.calculate(df, fye_map)
    assert result.iloc[0] == "Q2"  # AAPL, 2023-01-31, FYE 0930
    assert result.iloc[1] == "Q3"  # AAPL, 2023-04-30, FYE 0930
    assert result.iloc[2] == "Q1"  # MSFT, 2023-09-30, FYE 0630
    assert result.iloc[3] == "Q2"  # MSFT, 2023-12-31, FYE 0630

    # Edge case: within tolerance
    data_tolerance = {
        "cik10": ["AAPL"],
        "end": pd.to_datetime(["2023-10-07"]),  # Within 7 days of 0930 (Q4)
    }
    df_tolerance = pd.DataFrame(data_tolerance)
    result_tolerance = calculator.calculate(df_tolerance, fye_map)
    assert result_tolerance.iloc[0] == "Q4"
