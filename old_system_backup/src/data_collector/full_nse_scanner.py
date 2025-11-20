import pandas as pd
import yfinance as yf
import requests
import numpy as np
from datetime import datetime, timedelta
import time
import sys
import os
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import *

class FullNSEScanner:
    """
    (DEFENSIVE UPGRADE + TIER 2 ENHANCEMENT)
    Scans the entire market at the end of the day. This version includes robust parsing
    and validation to handle changes in the source data format from the NSE.
    
    UPGRADED with:
    - Enhanced ranking with tiered watchlists (Tier 2 - Upgrade 11)
    """
    
    def __init__(self, watchlist_file='data/daily_watchlist.csv'):
        print("🌐 FULL NSE MARKET SCANNER (UPGRADED - TIER 2)")
        print("=" * 50)
        print("Role: EOD screening with tiered watchlist generation.")
        print("=" * 50)
        self.watchlist_file = watchlist_file
        # UPGRADE 11: Additional watchlist files for tiers
        self.watchlist_top50 = 'data/watchlist_top50.csv'
        self.watchlist_mid200 = 'data/watchlist_mid200.csv'
        self.watchlist_low250 = 'data/watchlist_low250.csv'

    def _fetch_all_nse_stocks_robust(self):
        """
        (NEW DEFENSIVE METHOD)
        Fetches, validates, and parses all equity symbols. It is resilient to network
        errors, blocking, and minor changes in the source file format.
        """
        base_url = "https://www.nseindia.com/"
        data_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': base_url
        }

        for attempt in range(1, 4):
            try:
                print(f"Attempt {attempt}/3: Fetching full stock list...")
                session = requests.Session()
                session.get(base_url, headers=headers, timeout=15)
                time.sleep(1)
                response = session.get(data_url, headers=headers, timeout=20)
                response.raise_for_status()
                
                print("✅ Data download successful. Now parsing and validating...")

                try:
                    csv_data = pd.read_csv(io.StringIO(response.text.strip()))
                    csv_data.columns = [col.strip() for col in csv_data.columns]

                    required_cols = ['SYMBOL', 'SERIES']
                    if not all(col in csv_data.columns for col in required_cols):
                        print(f"❌ Parsing Error: The downloaded file is missing required columns. Found: {csv_data.columns.tolist()}")
                        return None

                    equity_symbols_df = csv_data[csv_data['SERIES'] == 'EQ']
                    
                    if equity_symbols_df.empty:
                        print("❌ Parsing Error: Found 0 stocks in the 'EQ' series. The file format may have changed.")
                        return None
                        
                    equity_symbols = equity_symbols_df['SYMBOL'].tolist()
                    
                    print(f"✅ Parsing successful. Found {len(equity_symbols)} equity symbols.")
                    return equity_symbols

                except Exception as e:
                    print(f"❌ CRITICAL PARSING FAILED after successful download: {e}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"❌ Network request failed on attempt {attempt}: {e}")
                if attempt < 3:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("❌ All network attempts to fetch the stock list have failed.")
                    return None
        return None

    def run_end_of_day_screening(self):
        """
        Fetches all ~2000+ NSE stocks, screens them, scores them, and saves the top 500.
        UPGRADED: Now creates tiered watchlists (Top 50, Mid 200, Low 250)
        """
        print(f"\n{'='*60}")
        print(f"🌙 RUNNING COMPREHENSIVE END-OF-DAY SCREENING (UPGRADED) - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        all_symbols = self._fetch_all_nse_stocks_robust()
        
        if not all_symbols:
            print("❌ CRITICAL FAILURE: Aborting EOD screening due to failure in fetching stock list.")
            print("🔄 Creating minimal fallback watchlist from hardcoded liquid stocks...")
            fallback_symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", 
                               "ITC", "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE", "TATAMOTORS", 
                               "MARUTI", "SUNPHARMA", "TATASTEEL", "HINDALCO", "INDUSINDBK", "TITAN",
                               "ADANIENT", "ADANIPORTS", "WIPRO", "ULTRACEMCO", "ASIANPAINT", "NESTLEIND",
                               "HCLTECH", "TECHM", "POWERGRID", "NTPC", "ONGC", "COALINDIA"]
            self._save_watchlist(fallback_symbols)
            print(f"⚠️ Saved minimal fallback watchlist with {len(fallback_symbols)} liquid stocks.")
            return fallback_symbols

        print(f"✅ Fetched {len(all_symbols)} total symbols from NSE. Now screening...")
        
        all_opportunities = []
        total_symbols = len(all_symbols)
        
        for i, symbol in enumerate(all_symbols):
            symbol_ns = f"{symbol}.NS"
            
            if i > 0 and i % 50 == 0:
                time.sleep(2)
                progress_msg = f"Progress: {i+1}/{total_symbols} ({symbol})"
                print(f"{progress_msg:<80}", end='\r')
            else:
                progress_msg = f"Progress: {i+1}/{total_symbols} ({symbol})"
                print(f"{progress_msg:<80}", end='\r')
            
            result = self.scan_stock(symbol_ns)
            
            if result:
                all_opportunities.append(result)

        print(f"\n\n✅ Screening complete. Found {len(all_opportunities)} stocks meeting basic criteria.")
        
        if not all_opportunities:
            print("⚠️ No stocks passed screening criteria.")
            print("🔄 Using previous day's watchlist or creating minimal fallback...")
            
            if os.path.exists(self.watchlist_file):
                print(f"✅ Keeping existing watchlist from: {self.watchlist_file}")
                return []
            else:
                fallback_symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
                self._save_watchlist(fallback_symbols)
                print(f"⚠️ Created minimal fallback watchlist with {len(fallback_symbols)} stocks.")
                return fallback_symbols

        sorted_opportunities = sorted(all_opportunities, key=lambda x: x['score'], reverse=True)
        
        # UPGRADE 11: Create tiered watchlists
        print(f"\n📊 Creating tiered watchlists...")
        
        top_50 = sorted_opportunities[:50]
        mid_200 = sorted_opportunities[50:250] if len(sorted_opportunities) > 50 else []
        low_250 = sorted_opportunities[250:500] if len(sorted_opportunities) > 250 else []
        
        # Extract symbols for each tier
        top_50_symbols = [stock['symbol'] for stock in top_50]
        mid_200_symbols = [stock['symbol'] for stock in mid_200]
        low_250_symbols = [stock['symbol'] for stock in low_250]
        
        # Save tiered watchlists
        self._save_tiered_watchlist(top_50_symbols, self.watchlist_top50, "TOP 50")
        if mid_200_symbols:
            self._save_tiered_watchlist(mid_200_symbols, self.watchlist_mid200, "MID 200")
        if low_250_symbols:
            self._save_tiered_watchlist(low_250_symbols, self.watchlist_low250, "LOW 250")
        
        # Also save full list (backward compatible with existing code)
        all_top_500_symbols = top_50_symbols + mid_200_symbols + low_250_symbols
        self._save_watchlist(all_top_500_symbols)
        
        # Display tier information
        print(f"\n{'='*60}")
        print("📊 TIERED WATCHLIST SUMMARY")
        print(f"{'='*60}")
        if top_50:
            print(f"🏆 TOP TIER (50 stocks)")
            print(f"   Score Range: {top_50[-1]['score']:.1f} - {top_50[0]['score']:.1f}")
            print(f"   File: {self.watchlist_top50}")
        
        if mid_200:
            print(f"⭐ MID TIER ({len(mid_200)} stocks)")
            print(f"   Score Range: {mid_200[-1]['score']:.1f} - {mid_200[0]['score']:.1f}")
            print(f"   File: {self.watchlist_mid200}")
        
        if low_250:
            print(f"✅ LOW TIER ({len(low_250)} stocks)")
            print(f"   Score Range: {low_250[-1]['score']:.1f} - {low_250[0]['score']:.1f}")
            print(f"   File: {self.watchlist_low250}")
        
        print(f"{'='*60}")
        print(f"\n💡 USAGE TIP:")
        print(f"   - Live scanner will prioritize TOP TIER first")
        print(f"   - If <3 opportunities found, scan MID TIER")
        print(f"   - Focus on quality over quantity!")
        print(f"{'='*60}")
        
        print(f"\n✅ Successfully generated and saved tiered watchlists for tomorrow's scans.")
        return sorted_opportunities[:50]  # Return top 50 for immediate use

    def _save_watchlist(self, symbols_list):
        """Saves the list of symbols to the watchlist CSV file."""
        try:
            dir_path = os.path.dirname(self.watchlist_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            df = pd.DataFrame(symbols_list, columns=['symbol'])
            df.to_csv(self.watchlist_file, index=False)
            print(f"📁 Main watchlist saved to {self.watchlist_file}")
        except Exception as e:
            print(f"❌ Error saving main watchlist: {e}")
    
    # UPGRADE 11: New method for saving tiered watchlists
    def _save_tiered_watchlist(self, symbols_list, filename, tier_name):
        """Saves a tiered watchlist with additional metadata"""
        try:
            dir_path = os.path.dirname(filename)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            df = pd.DataFrame(symbols_list, columns=['symbol'])
            df.to_csv(filename, index=False)
            print(f"📁 {tier_name} watchlist saved to {filename} ({len(symbols_list)} stocks)")
        except Exception as e:
            print(f"❌ Error saving {tier_name} watchlist: {e}")
    
    def scan_stock(self, symbol):
        """
        Analyzes a single stock and returns its data and score if it meets criteria.
        (This is the core analysis engine, now used by the new EOD process)
        """
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="2mo", interval="1d", auto_adjust=True)
            
            if df.empty or len(df) < 20:
                return None
            
            current_price = df['Close'].iloc[-1]
            
            avg_volume = df['Volume'].tail(20).mean()
            if pd.isna(avg_volume) or avg_volume == 0:
                return None
            
            avg_value = (avg_volume * current_price) / 10000000
            
            if avg_value < MIN_VOLUME_CR or current_price < MIN_PRICE or current_price > MAX_PRICE:
                return None
            
            if len(df) >= 6:
                momentum_5d = ((df['Close'].iloc[-1] / df['Close'].iloc[-5]) - 1) * 100
            else:
                momentum_5d = 0
            
            if len(df) >= 21:
                momentum_20d = ((df['Close'].iloc[-1] / df['Close'].iloc[-20]) - 1) * 100
            else:
                momentum_20d = 0
            
            today_change = ((df['Close'].iloc[-1] / df['Open'].iloc[-1]) - 1) * 100
            volatility = df['Close'].pct_change().std() * 100 * np.sqrt(252)
            
            if pd.isna(volatility):
                volatility = 0
            
            volume_ratio = df['Volume'].iloc[-1] / avg_volume if avg_volume > 0 else 0
            
            if len(df) >= 20:
                above_ma20 = current_price > df['Close'].rolling(20).mean().iloc[-1]
            else:
                above_ma20 = False
            
            score = 0
            if momentum_5d > 3:
                score += 25
            if momentum_20d > 5:
                score += 20
            if volume_ratio > 1.5:
                score += 20
            if above_ma20:
                score += 15
            if volatility > 30 and volatility < 100:
                score += 20
            
            if score > 30:
                return {
                    'symbol': symbol.replace('.NS', ''), 
                    'price': round(current_price, 2), 
                    'volume_cr': round(avg_value, 2), 
                    'today': round(today_change, 2), 
                    'momentum_5d': round(momentum_5d, 2), 
                    'momentum_20d': round(momentum_20d, 2), 
                    'volatility': round(volatility, 2), 
                    'volume_spike': round(volume_ratio, 2), 
                    'score': score
                }
        except Exception as e:
            return None
        return None
    
    # UPGRADE 11: New method to load tiered watchlist
    def load_tiered_watchlist(self, tier='top'):
        """
        Load specific tier of watchlist
        tier: 'top', 'mid', or 'low'
        """
        tier_files = {
            'top': self.watchlist_top50,
            'mid': self.watchlist_mid200,
            'low': self.watchlist_low250
        }
        
        filename = tier_files.get(tier, self.watchlist_top50)
        
        try:
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                symbols = df['symbol'].tolist()
                print(f"✅ Loaded {len(symbols)} stocks from {tier.upper()} tier")
                return symbols
            else:
                print(f"⚠️ {tier.upper()} tier file not found: {filename}")
                return None
        except Exception as e:
            print(f"❌ Error loading {tier.upper()} tier: {e}")
            return None

# To test the new functionality directly
if __name__ == "__main__":
    scanner = FullNSEScanner()
    scanner.run_end_of_day_screening()
    
    # Test loading tiered watchlists
    print("\n🧪 Testing tiered watchlist loading:")
    top_stocks = scanner.load_tiered_watchlist('top')
    if top_stocks:
        print(f"Top 5 from TOP tier: {top_stocks[:5]}")