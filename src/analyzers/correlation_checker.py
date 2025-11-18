"""
CORRELATION CHECKER MODULE
Prevents buying correlated stocks that move together
Part of Tier 2 Upgrades
"""

class CorrelationChecker:
    """
    Ensures true diversification by limiting correlated stocks
    Simple rule-based approach (no complex correlation calculations needed)
    """
    
    # Define stock groups that tend to move together
    CORRELATED_GROUPS = {
        'AUTO_MANUFACTURERS': ['TATAMOTORS', 'MARUTI', 'M&M', 'EICHERMOT', 'BAJAJ-AUTO', 'HEROMOTOCO'],
        'AUTO_ANCILLARIES': ['MOTHERSON', 'BOSCHLTD', 'MRF', 'APOLLOTYRE', 'CEATLTD', 'BALKRISIND'],
        
        'PRIVATE_BANKS': ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK'],
        'PSU_BANKS': ['SBIN', 'PNB', 'BANKBARODA', 'CANBK', 'UNIONBANK', 'BANKINDIA'],
        
        'IT_LARGE': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
        'IT_MID': ['LTIM', 'COFORGE', 'MPHASIS', 'PERSISTENT', 'LTTS'],
        
        'OIL_REFINING': ['RELIANCE', 'BPCL', 'IOC', 'MRPL'],
        'OIL_EXPLORATION': ['ONGC', 'OIL', 'GAIL'],
        
        'PHARMA_LARGE': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'LUPIN'],
        'PHARMA_MID': ['AUROPHARMA', 'BIOCON', 'TORNTPHARM', 'ALKEM', 'IPCALAB'],
        
        'STEEL': ['TATASTEEL', 'JSWSTEEL', 'SAIL', 'JINDALSTEL'],
        'METAL_MINING': ['HINDALCO', 'VEDL', 'COALINDIA', 'NMDC', 'HINDZINC'],
        
        'CEMENT': ['ULTRACEMCO', 'GRASIM', 'SHREECEM', 'AMBUJACEM', 'ACC'],
        
        'TELECOM': ['BHARTIARTL', 'IDEA', 'TATACOMM'],
        
        'POWER_GEN': ['NTPC', 'TATAPOWER', 'ADANIPOWER', 'TORNTPOWER'],
        'POWER_INFRA': ['POWERGRID', 'ADANIGREEN', 'ADANITRANS'],
        
        'REALTY': ['DLF', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'PHOENIXLTD'],
        
        'FMCG_LARGE': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA'],
        'FMCG_MID': ['DABUR', 'MARICO', 'GODREJCP', 'COLPAL', 'TATACONSUM'],
        
        'RETAIL': ['TITAN', 'TRENT', 'DMART', 'ABFRL'],
        
        'CHEMICALS': ['UPL', 'PIDILITIND', 'SRF', 'AARTI'],
        
        'ADANI_GROUP': ['ADANIENT', 'ADANIPORTS', 'ADANIGREEN', 'ADANIPOWER', 'ADANITRANS', 'ATGL'],
        'TATA_GROUP': ['TCS', 'TATAMOTORS', 'TATASTEEL', 'TATAPOWER', 'TATACONSUM'],
    }
    
    # Limits for each group type
    GROUP_LIMITS = {
        # Highly correlated sectors - max 1 stock
        'AUTO_MANUFACTURERS': 1,
        'PRIVATE_BANKS': 1,
        'PSU_BANKS': 1,
        'IT_LARGE': 1,
        'OIL_REFINING': 1,
        'STEEL': 1,
        'CEMENT': 1,
        'TELECOM': 1,
        'ADANI_GROUP': 1,
        
        # Moderately correlated - max 2 stocks
        'AUTO_ANCILLARIES': 2,
        'IT_MID': 2,
        'OIL_EXPLORATION': 2,
        'PHARMA_LARGE': 2,
        'PHARMA_MID': 2,
        'METAL_MINING': 2,
        'POWER_GEN': 2,
        'POWER_INFRA': 2,
        'REALTY': 2,
        'FMCG_LARGE': 2,
        'FMCG_MID': 2,
        'RETAIL': 2,
        'CHEMICALS': 2,
        'TATA_GROUP': 2,
    }
    
    def __init__(self):
        print("🔗 Correlation Checker initialized")
    
    def find_groups(self, symbol):
        """
        Find which correlation groups this stock belongs to
        
        Returns: list of group names
        """
        clean_symbol = symbol.replace('.NS', '').upper()
        groups = []
        
        for group_name, stocks in self.CORRELATED_GROUPS.items():
            if clean_symbol in stocks:
                groups.append(group_name)
        
        return groups
    
    def count_group_positions(self, group_name, open_positions):
        """Count how many positions are in a specific correlation group"""
        count = 0
        group_stocks = self.CORRELATED_GROUPS.get(group_name, [])
        
        for position in open_positions:
            clean_symbol = position['symbol'].replace('.NS', '').upper()
            if clean_symbol in group_stocks:
                count += 1
        
        return count
    
    def check_correlation_limit(self, new_symbol, open_positions):
        """
        Check if adding this stock would violate correlation limits
        
        Returns: (allowed: bool, reason: str, details: dict)
        """
        # Find which groups the new stock belongs to
        new_stock_groups = self.find_groups(new_symbol)
        
        if not new_stock_groups:
            # Stock not in any correlation group, allow
            return True, "Not in any correlation group", {}
        
        # Check each group for limits
        violations = []
        details = {}
        
        for group in new_stock_groups:
            current_count = self.count_group_positions(group, open_positions)
            limit = self.GROUP_LIMITS.get(group, 2)  # Default limit is 2
            
            details[group] = {
                'current': current_count,
                'limit': limit,
                'violated': current_count >= limit
            }
            
            if current_count >= limit:
                violations.append(f"{group} (limit: {limit}, current: {current_count})")
        
        if violations:
            reason = f"Correlation limit reached: {', '.join(violations)}"
            return False, reason, details
        
        return True, "Correlation check passed", details
    
    def get_existing_stocks_in_groups(self, group_names, open_positions):
        """Get list of stocks already held in specified groups"""
        existing = []
        
        for group in group_names:
            group_stocks = self.CORRELATED_GROUPS.get(group, [])
            for position in open_positions:
                clean_symbol = position['symbol'].replace('.NS', '').upper()
                if clean_symbol in group_stocks:
                    existing.append({
                        'symbol': clean_symbol,
                        'group': group
                    })
        
        return existing
    
    def display_correlation_status(self, open_positions):
        """Display current correlation group status"""
        print("\n" + "="*60)
        print("🔗 CORRELATION GROUP STATUS")
        print("="*60)
        
        # Check which groups have positions
        active_groups = {}
        
        for position in open_positions:
            groups = self.find_groups(position['symbol'])
            for group in groups:
                if group not in active_groups:
                    active_groups[group] = []
                active_groups[group].append(position['symbol'].replace('.NS', ''))
        
        if not active_groups:
            print("No positions in correlated groups")
            print("="*60)
            return
        
        # Display each active group
        for group, stocks in sorted(active_groups.items()):
            limit = self.GROUP_LIMITS.get(group, 2)
            count = len(stocks)
            
            # Status indicator
            if count >= limit:
                status = "🔴 FULL"
            elif count >= limit * 0.75:
                status = "🟡 NEAR LIMIT"
            else:
                status = "🟢 OK"
            
            stocks_str = ", ".join(stocks)
            print(f"{group:20} | {count}/{limit} | {status} | {stocks_str}")
        
        print("="*60)
    
    def suggest_alternatives(self, blocked_symbol, open_positions):
        """
        Suggest alternative stocks from different groups
        
        Returns: list of alternative symbols (not implemented fully, placeholder)
        """
        blocked_groups = self.find_groups(blocked_symbol)
        
        print(f"\n💡 {blocked_symbol} is blocked due to correlation.")
        print(f"   Groups: {', '.join(blocked_groups)}")
        print(f"   Consider stocks from different sectors/groups for better diversification.")
        
        return []
    
    def get_diversification_score(self, open_positions):
        """
        Calculate how well-diversified the portfolio is
        
        Returns: score from 0-100 (100 = perfect diversification)
        """
        if not open_positions:
            return 100
        
        # Count positions in correlation groups
        grouped_positions = 0
        
        for position in open_positions:
            groups = self.find_groups(position['symbol'])
            if groups:
                grouped_positions += 1
        
        # Count how many groups are at limit
        groups_at_limit = 0
        checked_groups = set()
        
        for position in open_positions:
            groups = self.find_groups(position['symbol'])
            for group in groups:
                if group not in checked_groups:
                    checked_groups.add(group)
                    count = self.count_group_positions(group, open_positions)
                    limit = self.GROUP_LIMITS.get(group, 2)
                    if count >= limit:
                        groups_at_limit += 1
        
        # Calculate score
        total_positions = len(open_positions)
        
        # Penalty for having many positions in same groups
        group_penalty = (grouped_positions / total_positions) * 30 if total_positions > 0 else 0
        
        # Penalty for groups at limit
        limit_penalty = groups_at_limit * 15
        
        score = max(0, 100 - group_penalty - limit_penalty)
        
        return round(score, 1)

# Test the module
if __name__ == "__main__":
    checker = CorrelationChecker()
    
    # Test group identification
    print("\n🧪 Testing correlation group identification:")
    test_stocks = ['TATAMOTORS', 'MARUTI', 'TCS', 'HDFCBANK', 'RELIANCE']
    for stock in test_stocks:
        groups = checker.find_groups(stock)
        print(f"  {stock}: {groups}")
    
    # Test correlation limits
    print("\n🧪 Testing correlation limits:")
    mock_positions = [
        {'symbol': 'TATAMOTORS', 'position_value': 12000},
    ]
    
    # Try to add another auto stock
    allowed, reason, details = checker.check_correlation_limit('MARUTI', mock_positions)
    print(f"\n  Can add MARUTI? {allowed}")
    print(f"  Reason: {reason}")
    print(f"  Details: {details}")
    
    # Display status
    checker.display_correlation_status(mock_positions)
    
    # Test diversification score
    score = checker.get_diversification_score(mock_positions)
    print(f"\n📊 Diversification Score: {score}/100")