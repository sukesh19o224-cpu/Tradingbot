"""
📊 EOD MANAGER V4.0
Manages 3-tier watchlist system:
- watchlist_top50.csv (Top liquid stocks)
- watchlist_mid200.csv (Mid-cap opportunities) 
- watchlist_low250.csv (Small-cap movers)

Also creates portfolio.json if missing
"""

import pandas as pd
import os
import json
from datetime import datetime


class EODManager:
    """
    Manages EOD scan outputs and creates necessary files
    """
    
    def __init__(self):
        self.data_dir = 'data'
        self.top50_file = f'{self.data_dir}/watchlist_top50.csv'
        self.mid200_file = f'{self.data_dir}/watchlist_mid200.csv'
        self.low250_file = f'{self.data_dir}/watchlist_low250.csv'
        self.combined_file = f'{self.data_dir}/daily_watchlist.csv'
        self.portfolio_file = f'{self.data_dir}/portfolio.json'
        self.yesterday_file = f'{self.data_dir}/yesterday_watchlist.json'
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def process_eod_results(self):
        """
        Process EOD scan results and create all necessary files
        Works with either 3-tier OR single daily_watchlist.csv
        """
        print("\n" + "="*70)
        print("📊 EOD MANAGER - Processing Results")
        print("="*70)
        
        # Check if using 3-tier system OR single file
        if os.path.exists(self.combined_file):
            print(f"✅ Found daily_watchlist.csv - Using single file mode")
            combined = self._load_watchlist(self.combined_file, "DAILY WATCHLIST")
        else:
            print(f"⚠️ No daily_watchlist.csv - Trying 3-tier mode...")
            # Step 1: Load all watchlists
            top50 = self._load_watchlist(self.top50_file, "TOP 50")
            mid200 = self._load_watchlist(self.mid200_file, "MID 200")
            low250 = self._load_watchlist(self.low250_file, "LOW 250")
            
            # Step 2: Combine watchlists
            combined = self._combine_watchlists(top50, mid200, low250)
        
        if combined.empty:
            print("⚠️ No watchlist data found!")
            return False
        
        # Add tier if missing (for single file mode)
        if 'tier' not in combined.columns:
            # Assign tiers based on score
            combined['tier'] = combined.apply(
                lambda row: 'TOP50' if row.name < 50 else 
                           ('MID200' if row.name < 250 else 'LOW250'), 
                axis=1
            )
        
        # Add score if missing
        if 'score' not in combined.columns:
            combined['score'] = 50  # Default score
        
        # Step 3: Create yesterday watchlist (for morning check)
        self._create_yesterday_watchlist(combined)
        
        # Step 4: Create/verify portfolio.json
        self._create_portfolio_if_missing()
        
        print("\n✅ EOD Processing Complete!")
        print("="*70)
        
        return True
    
    def _load_watchlist(self, filepath, name):
        """Load a single watchlist file"""
        if not os.path.exists(filepath):
            print(f"⚠️ {name} not found: {filepath}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(filepath)
            print(f"✅ Loaded {name}: {len(df)} stocks")
            return df
        except Exception as e:
            print(f"❌ Error loading {name}: {e}")
            return pd.DataFrame()
    
    def _combine_watchlists(self, top50, mid200, low250):
        """
        Combine all watchlists with priority system
        Priority: TOP50 > MID200 > LOW250
        """
        print("\n📊 Combining watchlists...")
        
        combined_list = []
        
        # Add TOP 50 (highest priority)
        if not top50.empty:
            for _, row in top50.iterrows():
                combined_list.append({
                    'symbol': row.get('symbol', row.get('Symbol', '')),
                    'score': row.get('score', row.get('Score', 100)),
                    'tier': 'TOP50',
                    'price': row.get('price', row.get('Price', 0))
                })
        
        # Add MID 200 (medium priority)
        if not mid200.empty:
            for _, row in mid200.iterrows():
                symbol = row.get('symbol', row.get('Symbol', ''))
                # Skip if already in list
                if not any(s['symbol'] == symbol for s in combined_list):
                    combined_list.append({
                        'symbol': symbol,
                        'score': row.get('score', row.get('Score', 75)),
                        'tier': 'MID200',
                        'price': row.get('price', row.get('Price', 0))
                    })
        
        # Add LOW 250 (lower priority)
        if not low250.empty:
            for _, row in low250.iterrows():
                symbol = row.get('symbol', row.get('Symbol', ''))
                # Skip if already in list
                if not any(s['symbol'] == symbol for s in combined_list):
                    combined_list.append({
                        'symbol': symbol,
                        'score': row.get('score', row.get('Score', 50)),
                        'tier': 'LOW250',
                        'price': row.get('price', row.get('Price', 0))
                    })
        
        df = pd.DataFrame(combined_list)
        
        if not df.empty:
            # Sort by score (highest first)
            df = df.sort_values('score', ascending=False)
            print(f"✅ Combined: {len(df)} total stocks")
            print(f"   TOP50: {len(df[df['tier']=='TOP50'])}")
            print(f"   MID200: {len(df[df['tier']=='MID200'])}")
            print(f"   LOW250: {len(df[df['tier']=='LOW250'])}")
        
        return df
    
    def _save_combined(self, df):
        """Save combined watchlist"""
        try:
            df.to_csv(self.combined_file, index=False)
            print(f"\n✅ Saved combined watchlist: {self.combined_file}")
            
            # Show top 10
            print("\n🏆 TOP 10 STOCKS FOR TOMORROW:")
            for i, row in df.head(10).iterrows():
                print(f"   {i+1}. {row['symbol']:12s} Score: {row['score']:3.0f}  "
                      f"Tier: {row['tier']:8s}  Price: ₹{row['price']:.2f}")
        
        except Exception as e:
            print(f"❌ Error saving combined watchlist: {e}")
    
    def _create_yesterday_watchlist(self, df):
        """
        Create yesterday_watchlist.json for morning check
        Takes top 20 stocks and fetches live prices if missing
        """
        try:
            top20 = df.head(20)
            
            watchlist = []
            print("\n📊 Preparing morning watchlist with live prices...")
            
            for idx, row in top20.iterrows():
                # Handle different column names
                symbol = row.get('symbol', row.get('Symbol', ''))
                score = row.get('score', row.get('Score', 50))
                tier = row.get('tier', row.get('Tier', 'GENERAL'))
                price = row.get('price', row.get('Price', row.get('close', row.get('Close', 0))))
                
                # If price is 0 or 100 (default), fetch live price
                if price == 0 or price == 100:
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(f"{symbol}.NS")
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            print(f"   Fetched price for {symbol}: ₹{price:.2f}")
                    except:
                        price = 100  # Fallback
                
                watchlist.append({
                    'symbol': symbol,
                    'score': float(score),
                    'tier': tier,
                    'price': float(price) if price > 0 else 100.0
                })
            
            with open(self.yesterday_file, 'w') as f:
                json.dump(watchlist, f, indent=2)
            
            print(f"\n✅ Created morning watchlist: {len(watchlist)} stocks")
            print(f"   File: {self.yesterday_file}")
            
            # Show top 5
            print("\n🏆 TOP 5 FOR MORNING CHECK:")
            for i, stock in enumerate(watchlist[:5], 1):
                print(f"   {i}. {stock['symbol']:12s} Score: {stock['score']:3.0f}  Price: ₹{stock['price']:.2f}")
        
        except Exception as e:
            print(f"❌ Error creating morning watchlist: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_portfolio_if_missing(self):
        """
        Create portfolio.json if it doesn't exist
        """
        if os.path.exists(self.portfolio_file):
            print(f"\n✅ Portfolio file exists: {self.portfolio_file}")
            return
        
        print(f"\n⚠️ Portfolio file missing - Creating new one...")
        
        from config.settings import INITIAL_CAPITAL
        
        initial_portfolio = {
            'capital': INITIAL_CAPITAL,
            'positions': {},
            'trade_history': [],
            'strategy_stats': {
                'MOMENTUM': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
                'MEAN_REVERSION': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
                'BREAKOUT': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
            },
            'last_updated': datetime.now().isoformat(),
            'created': datetime.now().isoformat()
        }
        
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(initial_portfolio, f, indent=4)
            
            print(f"✅ Created portfolio.json with ₹{INITIAL_CAPITAL:,.0f} capital")
        
        except Exception as e:
            print(f"❌ Error creating portfolio: {e}")
    
    def display_summary(self):
        """Display summary of current watchlists"""
        print("\n" + "="*70)
        print("📊 WATCHLIST SUMMARY")
        print("="*70)
        
        # Check each file
        files = [
            (self.top50_file, "TOP 50"),
            (self.mid200_file, "MID 200"),
            (self.low250_file, "LOW 250"),
            (self.combined_file, "COMBINED"),
            (self.yesterday_file, "MORNING CHECK"),
            (self.portfolio_file, "PORTFOLIO")
        ]
        
        for filepath, name in files:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                print(f"✅ {name:15s}: {modified.strftime('%Y-%m-%d %H:%M')}  ({size:,} bytes)")
            else:
                print(f"❌ {name:15s}: NOT FOUND")
        
        print("="*70)


def main():
    """Main function for standalone use"""
    print("""
    ╔═══════════════════════════════════════════════╗
    ║  EOD MANAGER V4.0                             ║
    ║  Processes 3-tier watchlist structure         ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    manager = EODManager()
    
    # Show current status
    manager.display_summary()
    
    print("\n" + "="*70)
    print("OPTIONS:")
    print("1. Process EOD Results (combine watchlists)")
    print("2. Show Summary Only")
    print("3. Create Portfolio.json (if missing)")
    print("4. Exit")
    print("="*70)
    
    choice = input("\nSelect option: ")
    
    if choice == "1":
        success = manager.process_eod_results()
        if success:
            manager.display_summary()
    
    elif choice == "2":
        manager.display_summary()
    
    elif choice == "3":
        manager._create_portfolio_if_missing()
    
    elif choice == "4":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid option")


if __name__ == "__main__":
    main()