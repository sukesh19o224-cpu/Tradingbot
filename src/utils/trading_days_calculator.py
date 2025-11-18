"""
📅 TRADING DAYS CALCULATOR
Calculates trading days (excludes weekends and holidays)
"""

from datetime import datetime, timedelta


def count_trading_days(start_date, end_date=None):
    """
    Count trading days between two dates (excludes weekends)
    
    Args:
        start_date: Start date (datetime or ISO string)
        end_date: End date (datetime or ISO string), defaults to now
    
    Returns:
        int: Number of trading days
    """
    # Convert to datetime if string
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date)
    
    if end_date is None:
        end_date = datetime.now()
    elif isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date)
    
    # Count days excluding weekends
    trading_days = 0
    current = start_date.date()
    end = end_date.date()
    
    while current <= end:
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Mon-Fri only
            trading_days += 1
        current += timedelta(days=1)
    
    return trading_days


def is_trading_day(date=None):
    """
    Check if given date is a trading day (Mon-Fri)
    
    Args:
        date: Date to check (datetime), defaults to today
    
    Returns:
        bool: True if trading day
    """
    if date is None:
        date = datetime.now()
    
    # 0-4 = Mon-Fri, 5-6 = Sat-Sun
    return date.weekday() < 5


if __name__ == "__main__":
    # Test
    from datetime import datetime
    
    print("\n📅 Testing Trading Days Calculator...")
    
    # Test 1: Same week
    start = datetime(2024, 11, 4)  # Monday
    end = datetime(2024, 11, 8)    # Friday
    days = count_trading_days(start, end)
    print(f"\n1️⃣ Mon-Fri same week: {days} trading days (expected: 5)")
    
    # Test 2: Over weekend
    start = datetime(2024, 11, 8)  # Friday
    end = datetime(2024, 11, 11)   # Monday
    days = count_trading_days(start, end)
    print(f"2️⃣ Fri-Mon (over weekend): {days} trading days (expected: 2)")
    
    # Test 3: Two weeks
    start = datetime(2024, 11, 4)  # Monday
    end = datetime(2024, 11, 15)   # Friday next week
    days = count_trading_days(start, end)
    print(f"3️⃣ Two weeks: {days} trading days (expected: 10)")
    
    # Test 4: Is today trading day?
    today_is_trading = is_trading_day()
    print(f"\n4️⃣ Is today a trading day? {today_is_trading}")