"""
SECTOR TRACKER MODULE
Tracks sector exposure to prevent concentration risk
Part of Tier 1 Upgrades
"""

class SectorTracker:
    """
    Tracks which sectors your positions belong to and enforces diversification limits
    """
    
    # Comprehensive sector mapping for top NSE stocks
    SECTOR_MAP = {
        # Banking & Financial Services
        'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'AXISBANK': 'Banking',
        'KOTAKBANK': 'Banking', 'SBIN': 'Banking', 'INDUSINDBK': 'Banking',
        'BANDHANBNK': 'Banking', 'FEDERALBNK': 'Banking', 'IDFCFIRSTB': 'Banking',
        'PNB': 'Banking', 'BANKBARODA': 'Banking', 'CANBK': 'Banking',
        
        'BAJFINANCE': 'NBFC', 'BAJAJFINSV': 'NBFC', 'CHOLAFIN': 'NBFC',
        'MUTHOOTFIN': 'NBFC', 'LICHSGFIN': 'NBFC',
        
        'HDFCLIFE': 'Insurance', 'SBILIFE': 'Insurance', 'ICICIPRULI': 'Insurance',
        
        # IT & Technology
        'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT',
        'TECHM': 'IT', 'LTIM': 'IT', 'COFORGE': 'IT', 'MPHASIS': 'IT',
        'PERSISTENT': 'IT', 'LTTS': 'IT',
        
        # Automotive
        'TATAMOTORS': 'Auto', 'MARUTI': 'Auto', 'M&M': 'Auto',
        'EICHERMOT': 'Auto', 'BAJAJ-AUTO': 'Auto', 'HEROMOTOCO': 'Auto',
        'TVSMOTOR': 'Auto', 'ASHOKLEY': 'Auto', 'ESCORTS': 'Auto',
        'MOTHERSON': 'Auto', 'BOSCHLTD': 'Auto', 'MRF': 'Auto',
        
        # Oil & Gas
        'RELIANCE': 'Oil & Gas', 'ONGC': 'Oil & Gas', 'BPCL': 'Oil & Gas',
        'IOC': 'Oil & Gas', 'GAIL': 'Oil & Gas', 'PETRONET': 'Oil & Gas',
        'OIL': 'Oil & Gas',
        
        # Pharmaceuticals
        'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
        'DIVISLAB': 'Pharma', 'AUROPHARMA': 'Pharma', 'LUPIN': 'Pharma',
        'BIOCON': 'Pharma', 'TORNTPHARM': 'Pharma', 'ALKEM': 'Pharma',
        
        # Metals & Mining
        'TATASTEEL': 'Metals', 'HINDALCO': 'Metals', 'JSWSTEEL': 'Metals',
        'VEDL': 'Metals', 'SAIL': 'Metals', 'COALINDIA': 'Metals',
        'NMDC': 'Metals', 'JINDALSTEL': 'Metals', 'HINDZINC': 'Metals',
        
        # FMCG
        'ITC': 'FMCG', 'HINDUNILVR': 'FMCG', 'NESTLEIND': 'FMCG',
        'BRITANNIA': 'FMCG', 'DABUR': 'FMCG', 'MARICO': 'FMCG',
        'GODREJCP': 'FMCG', 'COLPAL': 'FMCG', 'TATACONSUM': 'FMCG',
        
        # Cement
        'ULTRACEMCO': 'Cement', 'GRASIM': 'Cement', 'SHREECEM': 'Cement',
        'AMBUJACEM': 'Cement', 'ACC': 'Cement', 'JKCEMENT': 'Cement',
        
        # Telecom
        'BHARTIARTL': 'Telecom', 'IDEA': 'Telecom',
        
        # Power & Utilities
        'NTPC': 'Power', 'POWERGRID': 'Power', 'TATAPOWER': 'Power',
        'ADANIPOWER': 'Power', 'ADANIGREEN': 'Power', 'TORNTPOWER': 'Power',
        
        # Real Estate & Infrastructure
        'DLF': 'Realty', 'GODREJPROP': 'Realty', 'OBEROIRLTY': 'Realty',
        'PHOENIXLTD': 'Realty', 'PRESTIGE': 'Realty',
        
        'LT': 'Infra', 'ADANIPORTS': 'Infra', 'ADANIENT': 'Infra',
        
        # Chemicals
        'UPL': 'Chemicals', 'PIDILITIND': 'Chemicals', 'AARTI': 'Chemicals',
        'SRF': 'Chemicals',
        
        # Retail & Consumer
        'TITAN': 'Retail', 'TRENT': 'Retail', 'DMART': 'Retail',
        'ABFRL': 'Retail', 'SHOPERSTOP': 'Retail',
        
        # Airlines & Travel
        'INDIGO': 'Airlines',
        
        # Defense & Aerospace
        'HAL': 'Defense', 'BEL': 'Defense', 'BDL': 'Defense',
        
        # Misc
        'SUZLON': 'Renewable', 'IRCTC': 'Transport', 'CONCOR': 'Logistics',
    }
    
    # Sectors that need stricter limits (highly correlated)
    CONCENTRATED_SECTORS = ['Banking', 'Auto', 'IT', 'Oil & Gas', 'Metals']
    
    def __init__(self):
        print("📊 Sector Tracker initialized")
    
    def get_sector(self, symbol):
        """Get sector for a given stock symbol"""
        # Remove .NS suffix if present
        clean_symbol = symbol.replace('.NS', '').upper()
        return self.SECTOR_MAP.get(clean_symbol, 'Other')
    
    def calculate_sector_exposure(self, open_positions, total_capital):
        """
        Calculate current sector exposure as % of total capital
        
        Returns: dict of {sector: exposure_percent}
        """
        sector_values = {}
        
        for position in open_positions:
            sector = self.get_sector(position['symbol'])
            position_value = position.get('position_value', 0)
            
            if sector in sector_values:
                sector_values[sector] += position_value
            else:
                sector_values[sector] = position_value
        
        # Convert to percentages
        sector_exposure = {}
        for sector, value in sector_values.items():
            sector_exposure[sector] = (value / total_capital * 100) if total_capital > 0 else 0
        
        return sector_exposure
    
    def check_sector_limit(self, new_symbol, open_positions, total_capital, max_sector_exposure=0.40):
        """
        Check if adding this stock would violate sector exposure limits
        
        Returns: (allowed: bool, reason: str)
        """
        new_sector = self.get_sector(new_symbol)
        
        # Calculate current sector exposure
        sector_exposure = self.calculate_sector_exposure(open_positions, total_capital)
        
        current_exposure = sector_exposure.get(new_sector, 0)
        
        # Different limits for concentrated vs diversified sectors
        if new_sector in self.CONCENTRATED_SECTORS:
            # Stricter limit: Max 30% for concentrated sectors
            limit = 0.30
        else:
            # Standard limit: 40% for other sectors
            limit = max_sector_exposure
        
        if current_exposure >= (limit * 100):
            return False, f"Sector exposure limit reached: {new_sector} already at {current_exposure:.1f}% (limit: {limit*100:.0f}%)"
        
        return True, "Sector exposure OK"
    
    def count_sector_positions(self, sector, open_positions):
        """Count how many positions are in a given sector"""
        count = 0
        for position in open_positions:
            if self.get_sector(position['symbol']) == sector:
                count += 1
        return count
    
    def display_sector_allocation(self, open_positions, total_capital):
        """Display current sector allocation"""
        sector_exposure = self.calculate_sector_exposure(open_positions, total_capital)
        
        if not sector_exposure:
            print("No sector exposure (no open positions)")
            return
        
        print("\n" + "="*50)
        print("📊 SECTOR ALLOCATION")
        print("="*50)
        
        # Sort by exposure percentage
        sorted_sectors = sorted(sector_exposure.items(), key=lambda x: x[1], reverse=True)
        
        for sector, exposure in sorted_sectors:
            # Color code based on exposure level
            if exposure > 40:
                warning = "🔴 HIGH"
            elif exposure > 30:
                warning = "🟡 ELEVATED"
            else:
                warning = "🟢 OK"
            
            count = self.count_sector_positions(sector, open_positions)
            print(f"{sector:15} | {exposure:5.1f}% | {count} position(s) | {warning}")
        
        print("="*50)
    
    def get_sector_recommendations(self, open_positions, total_capital):
        """
        Suggest which sectors can still be added
        
        Returns: dict of {sector: 'AVAILABLE' or 'LIMITED' or 'FULL'}
        """
        sector_exposure = self.calculate_sector_exposure(open_positions, total_capital)
        recommendations = {}
        
        for sector in set(self.SECTOR_MAP.values()):
            current = sector_exposure.get(sector, 0)
            
            if sector in self.CONCENTRATED_SECTORS:
                limit = 30
            else:
                limit = 40
            
            if current >= limit:
                recommendations[sector] = 'FULL'
            elif current >= limit * 0.75:
                recommendations[sector] = 'LIMITED'
            else:
                recommendations[sector] = 'AVAILABLE'
        
        return recommendations

# Test the module
if __name__ == "__main__":
    tracker = SectorTracker()
    
    # Test sector identification
    print("\n🧪 Testing sector identification:")
    test_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'TATAMOTORS', 'UNKNOWN']
    for stock in test_stocks:
        sector = tracker.get_sector(stock)
        print(f"  {stock}: {sector}")
    
    # Test sector limits
    print("\n🧪 Testing sector limits:")
    mock_positions = [
        {'symbol': 'HDFCBANK', 'position_value': 15000},
        {'symbol': 'ICICIBANK', 'position_value': 15000},
    ]
    
    allowed, reason = tracker.check_sector_limit('AXISBANK', mock_positions, 100000)
    print(f"  Can add AXISBANK? {allowed}")
    print(f"  Reason: {reason}")
    
    # Display allocation
    tracker.display_sector_allocation(mock_positions, 100000)