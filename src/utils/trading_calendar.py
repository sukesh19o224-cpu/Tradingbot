"""
📅 Trading Calendar Utility
Calculate trading days excluding weekends and NSE holidays
"""

from datetime import datetime, timedelta
from typing import List

# NSE Holidays for 2024-2025
# Source: https://www.nseindia.com/regulations/holiday-master-2024
NSE_HOLIDAYS_2024 = [
    datetime(2024, 1, 26),  # Republic Day
    datetime(2024, 3, 8),   # Maha Shivaratri
    datetime(2024, 3, 25),  # Holi
    datetime(2024, 3, 29),  # Good Friday
    datetime(2024, 4, 11),  # Id-Ul-Fitr
    datetime(2024, 4, 17),  # Shri Ram Navami
    datetime(2024, 4, 21),  # Mahavir Jayanti
    datetime(2024, 5, 1),   # Maharashtra Day
    datetime(2024, 6, 17),  # Bakri Id
    datetime(2024, 7, 17),  # Moharram
    datetime(2024, 8, 15),  # Independence Day
    datetime(2024, 10, 2),  # Mahatma Gandhi Jayanti
    datetime(2024, 11, 1),  # Diwali
    datetime(2024, 11, 15), # Guru Nanak Jayanti
    datetime(2024, 12, 25), # Christmas
]

NSE_HOLIDAYS_2025 = [
    datetime(2025, 1, 26),  # Republic Day
    datetime(2025, 2, 26),  # Maha Shivaratri
    datetime(2025, 3, 14),  # Holi
    datetime(2025, 3, 31),  # Id-Ul-Fitr
    datetime(2025, 4, 10),  # Mahavir Jayanti
    datetime(2025, 4, 14),  # Dr. Ambedkar Jayanti
    datetime(2025, 4, 18),  # Good Friday
    datetime(2025, 5, 1),   # Maharashtra Day
    datetime(2025, 6, 7),   # Bakri Id
    datetime(2025, 8, 15),  # Independence Day
    datetime(2025, 8, 27),  # Ganesh Chaturthi
    datetime(2025, 10, 2),  # Mahatma Gandhi Jayanti
    datetime(2025, 10, 21), # Dussehra
    datetime(2025, 10, 24), # Diwali
    datetime(2025, 11, 5),  # Guru Nanak Jayanti
    datetime(2025, 12, 25), # Christmas
]

# Combine all holidays
NSE_HOLIDAYS = NSE_HOLIDAYS_2024 + NSE_HOLIDAYS_2025


def is_trading_day(date: datetime) -> bool:
    """
    Check if a given date is a trading day

    Args:
        date: Date to check

    Returns:
        True if it's a trading day (not weekend or holiday)
    """
    # Check if weekend (Saturday=5, Sunday=6)
    if date.weekday() in [5, 6]:
        return False

    # Check if NSE holiday
    date_only = datetime(date.year, date.month, date.day)
    if date_only in NSE_HOLIDAYS:
        return False

    return True


def calculate_trading_days(start_date: datetime, end_date: datetime = None) -> int:
    """
    Calculate number of trading days between two dates

    Args:
        start_date: Start date
        end_date: End date (default: today)

    Returns:
        Number of trading days (excluding weekends and holidays)
    """
    if end_date is None:
        end_date = datetime.now()

    # Ensure start_date is before end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    trading_days = 0
    current_date = start_date

    while current_date <= end_date:
        if is_trading_day(current_date):
            trading_days += 1
        current_date += timedelta(days=1)

    return trading_days


def get_next_trading_day(date: datetime) -> datetime:
    """
    Get the next trading day after a given date

    Args:
        date: Starting date

    Returns:
        Next trading day
    """
    next_day = date + timedelta(days=1)

    while not is_trading_day(next_day):
        next_day += timedelta(days=1)

    return next_day


def get_previous_trading_day(date: datetime) -> datetime:
    """
    Get the previous trading day before a given date

    Args:
        date: Starting date

    Returns:
        Previous trading day
    """
    prev_day = date - timedelta(days=1)

    while not is_trading_day(prev_day):
        prev_day -= timedelta(days=1)

    return prev_day


# Test the module
if __name__ == "__main__":
    print("📅 Trading Calendar Utility Test\n")

    # Test current date
    today = datetime.now()
    print(f"Today: {today.strftime('%Y-%m-%d %A')}")
    print(f"Is trading day: {is_trading_day(today)}\n")

    # Test trading days calculation
    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 31)
    trading_days = calculate_trading_days(start, end)
    print(f"Trading days in January 2025: {trading_days}")

    # Test from a specific date
    start = datetime(2025, 1, 15)
    trading_days = calculate_trading_days(start)
    print(f"Trading days since Jan 15, 2025: {trading_days}")

    # Test next/previous trading day
    test_date = datetime(2025, 1, 25)  # Saturday
    print(f"\nTest date: {test_date.strftime('%Y-%m-%d %A')}")
    print(f"Is trading day: {is_trading_day(test_date)}")
    print(f"Next trading day: {get_next_trading_day(test_date).strftime('%Y-%m-%d %A')}")
    print(f"Previous trading day: {get_previous_trading_day(test_date).strftime('%Y-%m-%d %A')}")
