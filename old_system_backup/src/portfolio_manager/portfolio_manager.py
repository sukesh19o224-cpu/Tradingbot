"""
📊 PORTFOLIO MANAGER V4.0 WITH GUI
Multi-strategy support + GUI interface
"""

import json
import os
from datetime import datetime
import sys
import yfinance as yf
import pandas as pd
import time
import tkinter as tk
from tkinter import ttk, messagebox
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import INITIAL_CAPITAL, TARGETS, MAX_HOLD_DAYS

# Import trading days calculator
try:
    from src.utils.trading_days_calculator import count_trading_days
    TRADING_DAYS_AVAILABLE = True
except:
    TRADING_DAYS_AVAILABLE = False
    print("⚠️ Trading days calculator not available, using calendar days")

# Import discord alerts
try:
    from src.alert_dispatcher.discord_alerts import DiscordAlerts
    DISCORD_AVAILABLE = True
except:
    DISCORD_AVAILABLE = False
    print("⚠️ Discord alerts not available")


class PortfolioManager:
    """
    Manages trading portfolio with multi-strategy support
    
    V4.0 NEW:
    - Tracks strategy per position
    - Strategy-specific exit logic
    - Per-strategy P&L tracking
    """
    
    def __init__(self, portfolio_file='data/portfolio.json'):
        self.portfolio_file = portfolio_file
        self.capital = 0
        self.available_capital = 0
        self.invested_capital = 0
        self.positions = {}
        self.trade_history = []
        
        # V4.0 NEW: Strategy tracking (V5.0 added POSITIONAL)
        self.strategy_stats = {
            'MOMENTUM': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'MEAN_REVERSION': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'BREAKOUT': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'POSITIONAL': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}  # V5.0: Monthly trading
        }
        
        # Initialize Discord alerts
        if DISCORD_AVAILABLE:
            self.discord = DiscordAlerts()
        else:
            self.discord = None
        
        print("📈 PORTFOLIO MANAGER V4.0 (GUI) Initializing...")
        self._load_portfolio()
    
    def _load_portfolio(self):
        """Load portfolio from file"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.capital = data.get('capital', INITIAL_CAPITAL)
                    self.positions = data.get('positions', {})
                    self.trade_history = data.get('trade_history', [])
                    self.strategy_stats = data.get('strategy_stats', self.strategy_stats)
                print(f"✅ Portfolio loaded from {self.portfolio_file}")
                self._recalculate_capital()
            except Exception as e:
                print(f"❌ Error loading portfolio: {e}")
                self._initialize_fresh_portfolio()
        else:
            print("⚠️ No portfolio file found. Initializing fresh.")
            self._initialize_fresh_portfolio()
    
    def _initialize_fresh_portfolio(self):
        """Initialize new portfolio"""
        self.capital = INITIAL_CAPITAL
        self.available_capital = INITIAL_CAPITAL
        self.invested_capital = 0
        self.positions = {}
        self.trade_history = []
        self.strategy_stats = {
            'MOMENTUM': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'MEAN_REVERSION': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'BREAKOUT': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'POSITIONAL': {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}  # V5.0
        }
        self._save_portfolio()
    
    def _save_portfolio(self):
        """Save portfolio to file"""
        lock_file = self.portfolio_file + '.lock'
        max_wait = 5
        wait_time = 0
        
        while os.path.exists(lock_file) and wait_time < max_wait:
            time.sleep(0.1)
            wait_time += 0.1
        
        try:
            with open(lock_file, 'w') as lock:
                lock.write(str(os.getpid()))
            
            data = {
                'capital': self.capital,
                'positions': self.positions,
                'trade_history': self.trade_history,
                'strategy_stats': self.strategy_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.portfolio_file) if os.path.dirname(self.portfolio_file) else '.', exist_ok=True)
            
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            # NEW V4.0+: Sync to database and create backup (dual-write mode)
            try:
                from src.utils.database import get_database
                from src.utils.health_monitor import get_backup_manager
                
                # Sync positions to database
                db = get_database()
                db.sync_positions_from_json(self.positions)
                
                # Create backup (only if significant change, to avoid too many backups)
                if len(self.positions) > 0 or len(self.trade_history) > 0:
                    backup_mgr = get_backup_manager()
                    backup_mgr.backup_portfolio(self.portfolio_file)
            except Exception as e:
                pass  # Silent fail - won't break existing functionality
        finally:
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass
    
    def _recalculate_capital(self):
        """Recalculate invested and available capital based on CURRENT holdings"""
        # Calculate invested based on remaining shares only
        self.invested_capital = 0
        for pos in self.positions.values():
            # Cost basis per share
            cost_per_share = pos['position_value'] / pos['initial_shares']
            # Invested = remaining shares × cost per share
            self.invested_capital += (pos['shares'] * cost_per_share)
        
        self.available_capital = self.capital - self.invested_capital
    
    def add_position(self, symbol, entry_price, shares, stop_loss, target1, target2, 
                     strategy='MOMENTUM', target3=None):
        """Add new position with strategy tracking"""
        if shares <= 0:
            print(f"❌ Invalid shares: {shares}")
            return False
        
        if entry_price <= 0:
            print(f"❌ Invalid price: {entry_price}")
            return False
        
        position_value = entry_price * shares
        
        if self.is_position_open(symbol):
            print(f"❌ Position already open: {symbol}")
            return False
        
        if position_value > self.available_capital:
            print(f"❌ Insufficient capital: Need ₹{position_value:,.0f}, Have ₹{self.available_capital:,.0f}")
            return False
        
        new_position = {
            'symbol': symbol,
            'shares': shares,
            'initial_shares': shares,
            'entry_price': entry_price,
            'position_value': position_value,
            'entry_time': datetime.now().isoformat(),
            'stop_loss': stop_loss,
            'status': 'OPEN',
            'targets_hit': [],
            'target1': target1,
            'target2': target2,
            'target3': target3 if target3 else target2 * 1.5,
            'strategy': strategy,
            'days_held': 0,
            'highest_price': entry_price
        }
        
        self.positions[symbol] = new_position
        self._recalculate_capital()
        self._save_portfolio()
        
        # Silent mode - no GUI popups (for auto mode)
        print(f"✅ Position added: {shares} shares of {symbol} ({strategy})")
        
        return True
    
    def remove_position(self, symbol, exit_price, reason="Closed"):
        """Remove position and track strategy stats"""
        if not self.is_position_open(symbol):
            try:
                messagebox.showerror("Error", f"No position found: {symbol}")
            except:
                print(f"❌ No position found: {symbol}")
            return False, None
        
        position = self.positions.pop(symbol)
        remaining_shares = position['shares']
        exit_value = exit_price * remaining_shares
        
        if position['initial_shares'] == 0:
            print(f"❌ Invalid position data for {symbol}")
            return False, None
        
        cost_basis_per_share = position['position_value'] / position['initial_shares']
        cost_of_remaining = cost_basis_per_share * remaining_shares
        pnl = exit_value - cost_of_remaining
        
        self.capital += pnl
        
        trade_log = {
            'symbol': position['symbol'],
            'strategy': position.get('strategy', 'MOMENTUM'),
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'shares': remaining_shares,
            'initial_shares': position.get('initial_shares', remaining_shares),
            'pnl': pnl,
            'pnl_percent': (pnl / cost_of_remaining) * 100 if cost_of_remaining > 0 else 0,
            'profit_loss': pnl,
            'profit_loss_percent': (pnl / cost_of_remaining) * 100 if cost_of_remaining > 0 else 0,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now().isoformat(),
            'exit_reason': reason,
            'reason': reason,
            'hold_days': position.get('days_held', 0),
            'stop_loss': position.get('stop_loss'),
            'highest_price': position.get('highest_price'),
            'targets_hit': position.get('targets_hit', [])
        }
        self.trade_history.append(trade_log)
        
        # NEW V4.0+: Save to database (dual-write mode)
        try:
            from src.utils.database import get_database
            db = get_database()
            db.add_trade(trade_log)
        except Exception as e:
            pass  # Silent fail - won't break existing functionality
        
        # Update strategy stats
        strategy = position.get('strategy', 'MOMENTUM')
        if strategy in self.strategy_stats:
            self.strategy_stats[strategy]['trades'] += 1
            self.strategy_stats[strategy]['pnl'] += pnl
            
            if pnl > 0:
                self.strategy_stats[strategy]['wins'] += 1
            else:
                self.strategy_stats[strategy]['losses'] += 1
        
        self._recalculate_capital()
        self._save_portfolio()
        
        alert_data = {
            'symbol': symbol,
            'strategy': strategy,
            'action': f"SELL ({reason})",
            'exit_price': exit_price,
            'profit_loss': pnl,
            'return_percent': trade_log['pnl_percent'],
            'reason': reason
        }
        
        print(f"✅ Position closed: {symbol} ({strategy}), P&L: ₹{pnl:,.2f}")
        
        # Send Discord alert
        if self.discord:
            self.discord.send_exit_alert(alert_data)
        
        return True, alert_data
    
    def manual_remove_position(self, symbol):
        """Manually remove position without P&L"""
        if not self.is_position_open(symbol):
            return False
        self.positions.pop(symbol)
        self._recalculate_capital()
        self._save_portfolio()
        return True
    
    def is_position_open(self, symbol):
        """Check if position is open"""
        symbol_normalized = symbol.upper().replace('.NS', '')
        for key in self.positions.keys():
            if key.upper().replace('.NS', '') == symbol_normalized:
                return True
        return False
    
    def get_open_positions(self):
        """Get all open positions"""
        return list(self.positions.values())
    
    def get_positions_by_strategy(self, strategy):
        """Get positions for specific strategy"""
        return [pos for pos in self.positions.values() if pos.get('strategy') == strategy]
    
    def display_summary(self):
        """Display portfolio summary"""
        print("\n" + "="*70)
        print("📊 PORTFOLIO SUMMARY V4.0")
        print("="*70)
        print(f"💰 Total Capital:     ₹{self.capital:,.2f}")
        print(f"💵 Invested:          ₹{self.invested_capital:,.2f}")
        print(f"💵 Available:         ₹{self.available_capital:,.2f}")
        print(f"📈 Open Positions:    {len(self.positions)}")
        
        if self.positions:
            print(f"\n📊 Positions by Strategy:")
            for strategy in ['MOMENTUM', 'MEAN_REVERSION', 'BREAKOUT', 'POSITIONAL']:
                count = len(self.get_positions_by_strategy(strategy))
                if count > 0:
                    print(f"   {strategy:15s}: {count} positions")
        
        print("="*70)
    
    def display_strategy_stats(self):
        """Display per-strategy performance"""
        print("\n" + "="*70)
        print("📊 STRATEGY PERFORMANCE")
        print("="*70)
        
        for strategy, stats in self.strategy_stats.items():
            trades = stats['trades']
            if trades == 0:
                continue
            
            wins = stats['wins']
            losses = stats['losses']
            win_rate = (wins / trades) * 100 if trades > 0 else 0
            pnl = stats['pnl']
            
            print(f"\n{strategy}:")
            print(f"   Trades: {trades} (W: {wins}, L: {losses})")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   P&L: ₹{pnl:,.0f}")
            
            if pnl > 0:
                print(f"   Status: ✅ Profitable")
            elif pnl < 0:
                print(f"   Status: ⚠️ Losing")
            else:
                print(f"   Status: ⚪ Neutral")
        
        print("="*70)
    
    def update_positions_from_live_data(self, multi_strategy_manager=None):
        """Update positions with live data"""
        if not self.positions:
            return []
        
        print(f"🔍 Checking {len(self.positions)} positions...")
        alerts_to_send = []
        symbols_to_check = list(self.positions.keys())
        
        for symbol in symbols_to_check:
            position = self.positions.get(symbol)
            if not position:
                continue
            
            symbol_normalized = symbol.replace('.NS', '')
            symbol_ns = f"{symbol_normalized}.NS"
            
            # Get days held from position
            days_held = position.get('days_held', 0)
            
            try:
                live_data = yf.Ticker(symbol_ns).history(period='1d')
                
                if live_data.empty:
                    print(f"⚠️ {symbol_normalized}: No data available")
                    continue
                
                current_price = live_data['Close'].iloc[-1]
                old_highest = position.get('highest_price', position['entry_price'])
                
                if current_price > old_highest:
                    position['highest_price'] = current_price
                    print(f"📈 {symbol_normalized}: Updated highest ₹{old_highest:.2f} → ₹{current_price:.2f}")
                
                profit_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
                print(f"💹 {symbol_normalized}: Entry ₹{position['entry_price']:.2f}, Current ₹{current_price:.2f} ({profit_pct:+.1f}%), Days: {days_held}")
                
                # Show target status
                targets_hit = position.get('targets_hit', [])
                if targets_hit:
                    status = " | ".join([f"{t}✅" for t in targets_hit])
                    remaining_targets = [t for t in ['T1', 'T2', 'T3'] if t not in targets_hit]
                    if remaining_targets:
                        status += f" | Waiting: {', '.join(remaining_targets)}"
                    print(f"   📊 Targets: {status}")
                
                # Use strategy-specific trailing stop
                if multi_strategy_manager:
                    new_stop = multi_strategy_manager.update_position_stops(position, current_price)
                    position['stop_loss'] = new_stop
                else:
                    # Default trailing
                    if profit_pct >= 12:
                        position['stop_loss'] = max(position['stop_loss'], position['entry_price'] * 1.08)
                    elif profit_pct >= 8:
                        position['stop_loss'] = max(position['stop_loss'], position['entry_price'] * 1.05)
                    elif profit_pct >= 6:
                        position['stop_loss'] = max(position['stop_loss'], position['entry_price'] * 1.03)
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    _, alert_data = self.remove_position(symbol_normalized, position['stop_loss'], "Stop Loss")
                    if alert_data:
                        alerts_to_send.append(alert_data)
                    continue
                
                # Update days held (TRADING DAYS)
                entry_time = datetime.fromisoformat(position['entry_time'])
                
                if TRADING_DAYS_AVAILABLE:
                    days_held = count_trading_days(entry_time, datetime.now())
                else:
                    days_held = (datetime.now() - entry_time).days
                
                position['days_held'] = days_held
                
                # Strategy-specific exit check
                if multi_strategy_manager:
                    should_exit, reason, exit_price = multi_strategy_manager.check_exit_conditions(
                        position, current_price, days_held
                    )
                    if should_exit:
                        _, alert_data = self.remove_position(symbol_normalized, exit_price, reason)
                        if alert_data:
                            alerts_to_send.append(alert_data)
                        continue
                else:
                    if days_held >= MAX_HOLD_DAYS:
                        _, alert_data = self.remove_position(symbol_normalized, current_price, f"Max Hold ({days_held} trading days)")
                        if alert_data:
                            alerts_to_send.append(alert_data)
                        continue
                
                # Check targets (partial exits)
                if not TARGETS:
                    continue
                
                # Debug: Check if initial_shares exists
                if 'initial_shares' not in position:
                    position['initial_shares'] = position['shares']
                    print(f"⚠️ {symbol_normalized}: Added missing initial_shares")
                
                for target_name, target_info in sorted(TARGETS.items()):
                    target_price = position['entry_price'] * (1 + target_info['level'])
                    
                    if current_price >= target_price and target_name not in position.get('targets_hit', []):
                        shares_to_sell = round(position['initial_shares'] * target_info['exit_percent'])
                        shares_to_sell = min(shares_to_sell, position['shares'])
                        shares_to_sell = round(position['initial_shares'] * target_info['exit_percent'])
                        shares_to_sell = min(shares_to_sell, position['shares'])
                        
                        if shares_to_sell <= 0:
                            print(f"⚠️ {symbol_normalized}: Can't sell {target_name} - shares_to_sell = {shares_to_sell}")
                            continue
                        
                        position['shares'] -= shares_to_sell
                        
                        cost_basis_per_share = position['position_value'] / position['initial_shares']
                        cost_of_sold = cost_basis_per_share * shares_to_sell
                        exit_value = target_price * shares_to_sell
                        pnl = exit_value - cost_of_sold
                        
                        # Return the exit value to capital
                        self.capital += exit_value
                        # Reduce invested by cost basis of sold shares
                        self.invested_capital -= cost_of_sold
                        
                        if 'targets_hit' not in position:
                            position['targets_hit'] = []
                        position['targets_hit'].append(target_name)
                        
                        # Update strategy stats for partial
                        strategy = position.get('strategy', 'MOMENTUM')
                        if strategy in self.strategy_stats:
                            self.strategy_stats[strategy]['pnl'] += pnl
                        
                        alert_data = {
                            'symbol': symbol_normalized,
                            'strategy': strategy,
                            'action': f"SELL PARTIAL ({target_name})",
                            'exit_price': target_price,
                            'profit_loss': pnl,
                            'return_percent': (pnl / cost_of_sold) * 100 if cost_of_sold > 0 else 0,
                            'reason': f"{target_name} Reached"
                        }
                        alerts_to_send.append(alert_data)
                        
                        remaining_shares = position['shares']
                        print(f"✅ {target_name} HIT: Sold {shares_to_sell}/{position['initial_shares']} shares at ₹{target_price:.2f}, P&L: ₹{pnl:+,.0f} | Remaining: {remaining_shares}")
                        
                        if position['shares'] <= 0:
                            self.positions.pop(symbol)
                            break
            
            except Exception as e:
                print(f"⚠️ Error updating {symbol}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        # Recalculate capital after all updates
        self._recalculate_capital()
        self._save_portfolio()
        return alerts_to_send


def _fetch_nse_symbols():
    """Fetch stock symbols for auto-suggestion"""
    try:
        base_url = "https://www.nseindia.com/"
        api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        headers = {'User-Agent': 'Mozilla/5.0'}
        with requests.Session() as s:
            s.get(base_url, headers=headers, timeout=5)
            time.sleep(0.5)
            response = s.get(api_url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            return [item['symbol'] for item in data['data']]
    except:
        return []


class PortfolioGUI(tk.Tk):
    """GUI for Portfolio Manager V4.0"""
    
    def __init__(self, portfolio_manager):
        super().__init__()
        self.pm = portfolio_manager
        
        self.title("Portfolio Manager V4.0 (Multi-Strategy)")
        self.geometry("900x700")
        
        self.all_symbols = _fetch_nse_symbols()
        self.symbol_var = tk.StringVar()
        
        self._create_widgets()
        self.refresh_all()
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Summary frame
        summary_frame = ttk.LabelFrame(self, text="Portfolio Summary")
        summary_frame.pack(padx=10, pady=5, fill="x")
        
        # Positions frame
        positions_frame = ttk.LabelFrame(self, text="Open Positions")
        positions_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Actions frame
        actions_frame = ttk.LabelFrame(self, text="Actions")
        actions_frame.pack(padx=10, pady=5, fill="x")
        
        # Summary labels
        self.summary_labels = {}
        summary_items = [
            "Total Capital", 
            "Starting Capital",
            "Total Profit",
            "Invested Capital", 
            "Available Capital", 
            "Current Value", 
            "Total P&L (Open)", 
            "Open Positions",
            "Closed Trades",
            "Win Rate"
        ]
        for i, text in enumerate(summary_items):
            ttk.Label(summary_frame, text=f"{text}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.summary_labels[text] = ttk.Label(summary_frame, text="₹0.00", font=("Arial", 10, "bold"))
            self.summary_labels[text].grid(row=i, column=1, sticky="w", padx=5, pady=2)
        
        # Positions tree
        columns = ("Symbol", "Strategy", "Initial", "Holding", "Entry", "Current", "Curr.Val", "P&L", "SL", "Days")
        self.tree = ttk.Treeview(positions_frame, columns=columns, show='headings', height=15)
        
        # Column widths
        col_widths = {
            "Symbol": 80,
            "Strategy": 80,
            "Initial": 60,
            "Holding": 60,
            "Entry": 70,
            "Current": 70,
            "Curr.Val": 90,
            "P&L": 120,
            "SL": 70,
            "Days": 50
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col], anchor="center")
        
        scrollbar = ttk.Scrollbar(positions_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buy frame
        buy_frame = ttk.LabelFrame(actions_frame, text="ADD POSITION (Manual)")
        buy_frame.pack(side="left", padx=5, pady=5, fill="both", expand=True)
        
        # Sell frame
        sell_frame = ttk.LabelFrame(actions_frame, text="REMOVE POSITION")
        sell_frame.pack(side="right", padx=5, pady=5)
        
        # Entry fields
        labels = ["Symbol", "Entry Price", "Shares", "Stop Loss", "Target 1", "Target 2", "Strategy"]
        self.entries = {}
        
        for i, label in enumerate(labels):
            ttk.Label(buy_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            if label == "Symbol":
                entry = ttk.Entry(buy_frame, width=15, textvariable=self.symbol_var)
                self.symbol_var.trace("w", self.update_suggestion_list)
            elif label == "Strategy":
                entry = ttk.Combobox(buy_frame, width=13, values=["MOMENTUM", "MEAN_REVERSION", "BREAKOUT", "POSITIONAL"])
                entry.set("MOMENTUM")
            else:
                entry = ttk.Entry(buy_frame, width=15)
            
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[label] = entry
        
        # Suggestion list
        self.suggestion_list = tk.Listbox(buy_frame, height=5)
        self.suggestion_list.grid(row=0, column=2, rowspan=4, padx=5, pady=2, sticky="ns")
        self.suggestion_list.bind("<<ListboxSelect>>", self.on_suggestion_select)
        
        # Buttons
        ttk.Button(buy_frame, text="Add Position", command=self.add_position).grid(
            row=len(labels), column=0, columnspan=2, pady=5)
        
        ttk.Button(sell_frame, text="Remove Selected\n(Manual Close)", 
                  command=self.remove_position).pack(padx=10, pady=10)
        
        ttk.Button(sell_frame, text="View Strategy Stats", 
                  command=self.show_strategy_stats).pack(padx=10, pady=5)
    
    def update_suggestion_list(self, *args):
        """Update symbol suggestions"""
        search_term = self.symbol_var.get().upper()
        self.suggestion_list.delete(0, tk.END)
        if not search_term:
            return
        
        matches = [s for s in self.all_symbols if s.startswith(search_term)]
        for match in matches[:10]:
            self.suggestion_list.insert(tk.END, match)
    
    def on_suggestion_select(self, event):
        """Handle suggestion selection"""
        if not self.suggestion_list.curselection():
            return
        selected = self.suggestion_list.get(self.suggestion_list.curselection())
        self.symbol_var.set(selected)
        self.suggestion_list.delete(0, tk.END)
    
    def refresh_all(self):
        """Refresh all displays with live data"""
        # Update days held for all positions
        for symbol, pos in self.pm.positions.items():
            if 'entry_time' in pos:
                entry_time = datetime.fromisoformat(pos['entry_time'])
                
                # Calculate TRADING days (exclude weekends)
                if TRADING_DAYS_AVAILABLE:
                    pos['days_held'] = count_trading_days(entry_time, datetime.now())
                else:
                    # Fallback to calendar days
                    pos['days_held'] = (datetime.now() - entry_time).days
            else:
                # Old position without entry_time - set to today
                pos['entry_time'] = datetime.now().isoformat()
                pos['days_held'] = 0
        self.pm._save_portfolio()
        
        # Calculate comprehensive stats
        starting_capital = INITIAL_CAPITAL
        total_profit = self.pm.capital - starting_capital
        
        # Calculate closed trades stats
        total_trades = sum(stats['trades'] for stats in self.pm.strategy_stats.values())
        total_wins = sum(stats['wins'] for stats in self.pm.strategy_stats.values())
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        # Update summary
        self.summary_labels["Total Capital"].config(
            text=f"₹{self.pm.capital:,.2f}",
            foreground='green' if total_profit > 0 else 'red'
        )
        self.summary_labels["Starting Capital"].config(text=f"₹{starting_capital:,.2f}")
        self.summary_labels["Total Profit"].config(
            text=f"₹{total_profit:+,.2f} ({total_profit/starting_capital*100:+.1f}%)",
            foreground='green' if total_profit > 0 else 'red'
        )
        self.summary_labels["Invested Capital"].config(text=f"₹{self.pm.invested_capital:,.2f}")
        self.summary_labels["Available Capital"].config(text=f"₹{self.pm.available_capital:,.2f}")
        self.summary_labels["Open Positions"].config(text=str(len(self.pm.positions)))
        self.summary_labels["Closed Trades"].config(text=str(total_trades))
        self.summary_labels["Win Rate"].config(
            text=f"{win_rate:.1f}% ({total_wins}/{total_trades})",
            foreground='green' if win_rate >= 50 else 'red'
        )
        
        # Calculate total current value and P&L
        total_current_value = 0
        total_pnl = 0
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add positions with live data
        import yfinance as yf
        for pos in self.pm.get_open_positions():
            symbol = pos['symbol']
            days = pos.get('days_held', 0)
            entry = pos['entry_price']
            shares = pos['shares']
            strategy = pos.get('strategy', 'MOMENTUM')
            
            # Fetch current price
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
            except:
                current_price = entry  # Fallback to entry if fetch fails
            
            # Calculate P&L based on REMAINING shares
            current_value = current_price * shares
            
            # Cost basis for remaining shares
            cost_per_share = pos['position_value'] / pos['initial_shares']
            remaining_cost = cost_per_share * shares
            
            pnl = current_value - remaining_cost
            pnl_percent = (pnl / remaining_cost) * 100 if remaining_cost > 0 else 0
            
            # Accumulate totals
            total_current_value += current_value
            total_pnl += pnl
            
            # Get initial shares (for display)
            initial_shares = pos.get('initial_shares', shares)
            
            # Color code P&L
            pnl_text = f"₹{pnl:+,.0f} ({pnl_percent:+.1f}%)"
            
            self.tree.insert("", "end", values=(
                symbol,
                strategy[:8],
                initial_shares,              # Initial shares
                shares,                       # Current holding
                f"₹{entry:.2f}",
                f"₹{current_price:.2f}",
                f"₹{current_value:,.0f}",
                pnl_text,
                f"₹{pos['stop_loss']:.2f}",
                f"{days}d"
            ), tags=('profit' if pnl > 0 else 'loss',))
        
        # Update summary with totals
        self.summary_labels["Current Value"].config(
            text=f"₹{total_current_value:,.2f}",
            foreground='green' if total_pnl > 0 else 'red'  # Green if profit, red if loss
        )
        
        total_pnl_percent = (total_pnl / self.pm.invested_capital * 100) if self.pm.invested_capital > 0 else 0
        self.summary_labels["Total P&L (Open)"].config(
            text=f"₹{total_pnl:+,.0f} ({total_pnl_percent:+.1f}%)",
            foreground='green' if total_pnl > 0 else 'red'
        )
        
        # Configure tag colors
        self.tree.tag_configure('profit', foreground='green')
        self.tree.tag_configure('loss', foreground='red')
        
        # Schedule next refresh (60 seconds)
        self.after(60000, self.refresh_all)
    
    def add_position(self):
        """Add position from GUI"""
        try:
            symbol = self.entries["Symbol"].get().upper()
            entry_price = float(self.entries["Entry Price"].get())
            shares = int(self.entries["Shares"].get())
            stop_loss = float(self.entries["Stop Loss"].get())
            target1 = float(self.entries["Target 1"].get())
            target2 = float(self.entries["Target 2"].get())
            strategy = self.entries["Strategy"].get()
            
            if not all([symbol, entry_price, shares, stop_loss, target1, target2, strategy]):
                messagebox.showerror("Error", "All fields required!")
                return
            
            if self.pm.add_position(symbol, entry_price, shares, stop_loss, target1, target2, strategy):
                self.refresh_all()
                for entry in self.entries.values():
                    if hasattr(entry, 'delete'):
                        entry.delete(0, tk.END)
                    elif hasattr(entry, 'set'):
                        entry.set("MOMENTUM")
        
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Check numbers!")
    
    def remove_position(self):
        """Remove selected position with P&L tracking"""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a position first!")
            return
        
        symbol = self.tree.item(selected)['values'][0]
        
        # Get current price for the position
        position = None
        for key, pos in self.pm.positions.items():
            if key.replace('.NS', '').upper() == symbol.upper():
                position = pos
                break
        
        if not position:
            messagebox.showerror("Error", "Position not found!")
            return
        
        # Ask for exit price
        exit_price_dialog = tk.Toplevel(self)
        exit_price_dialog.title(f"Exit {symbol}")
        exit_price_dialog.geometry("300x150")
        
        ttk.Label(exit_price_dialog, text=f"Exit {symbol}", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Label(exit_price_dialog, text=f"Entry: ₹{position['entry_price']:.2f}").pack()
        
        ttk.Label(exit_price_dialog, text="Exit Price:").pack(pady=5)
        exit_price_var = tk.StringVar(value=str(position['entry_price']))
        exit_entry = ttk.Entry(exit_price_dialog, textvariable=exit_price_var, width=15)
        exit_entry.pack()
        
        def confirm_exit():
            try:
                exit_price = float(exit_price_var.get())
                if exit_price <= 0:
                    messagebox.showerror("Error", "Invalid exit price!")
                    return
                
                success, alert_data = self.pm.remove_position(symbol, exit_price, "Manual Exit")
                if success:
                    exit_price_dialog.destroy()
                    self.refresh_all()
                    
                    pnl = alert_data['profit_loss']
                    pnl_pct = alert_data['return_percent']
                    messagebox.showinfo("Success", 
                        f"{symbol} closed!\n"
                        f"P&L: ₹{pnl:+,.0f} ({pnl_pct:+.1f}%)")
            except ValueError:
                messagebox.showerror("Error", "Invalid price format!")
        
        ttk.Button(exit_price_dialog, text="Confirm Exit", command=confirm_exit).pack(pady=10)
        
        exit_price_dialog.transient(self)
        exit_price_dialog.grab_set()
        exit_entry.focus()
        exit_entry.select_range(0, tk.END)
    
    def show_strategy_stats(self):
        """Show strategy performance"""
        stats_window = tk.Toplevel(self)
        stats_window.title("Strategy Performance")
        stats_window.geometry("400x300")
        
        text = tk.Text(stats_window, wrap="word", font=("Courier", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        text.insert("1.0", "📊 STRATEGY PERFORMANCE\n" + "="*40 + "\n\n")
        
        for strategy, stats in self.pm.strategy_stats.items():
            if stats['trades'] > 0:
                win_rate = (stats['wins'] / stats['trades']) * 100
                text.insert(tk.END, f"{strategy}:\n")
                text.insert(tk.END, f"  Trades: {stats['trades']} (W:{stats['wins']}, L:{stats['losses']})\n")
                text.insert(tk.END, f"  Win Rate: {win_rate:.1f}%\n")
                text.insert(tk.END, f"  P&L: ₹{stats['pnl']:,.0f}\n\n")
        
        text.config(state="disabled")


if __name__ == '__main__':
    pm = PortfolioManager()
    app = PortfolioGUI(portfolio_manager=pm)
    app.mainloop()