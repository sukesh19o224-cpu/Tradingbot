"""
📊 TRADING SYSTEM GUI - Live Portfolio Dashboard

Tkinter-based GUI showing:
- Portfolio summary (capital, invested, P&L)
- Open positions table
- Trade history logs
- Real-time updates
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from datetime import datetime
from typing import Dict, List
import threading
import time


class TradingDashboard:
    """Main GUI Dashboard for Trading System"""

    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Hybrid Trading System - Live Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')

        # Data files
        self.swing_portfolio_file = 'data/swing_portfolio.json'
        self.swing_trades_file = 'data/swing_trades.json'
        self.positional_portfolio_file = 'data/positional_portfolio.json'
        self.positional_trades_file = 'data/positional_trades.json'

        # Auto-refresh
        self.auto_refresh = True
        self.refresh_interval = 5000  # 5 seconds

        # Build UI
        self.create_ui()

        # Initial load
        self.refresh_data()

        # Start auto-refresh
        self.auto_refresh_data()

    def create_ui(self):
        """Create the main UI layout"""

        # Title
        title_frame = tk.Frame(self.root, bg='#2d2d2d', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = tk.Label(
            title_frame,
            text="🚀 HYBRID TRADING SYSTEM",
            font=('Arial', 24, 'bold'),
            bg='#2d2d2d',
            fg='#00ff00'
        )
        title_label.pack(pady=10)

        # Portfolio Summary Section
        self.create_summary_section()

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_swing_tab()
        self.create_positional_tab()
        self.create_logs_tab()

        # Control buttons at bottom
        self.create_control_panel()

    def create_summary_section(self):
        """Create portfolio summary section"""
        summary_frame = tk.Frame(self.root, bg='#2d2d2d')
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        # Summary cards
        self.create_summary_card(summary_frame, "💰 INITIAL CAPITAL", "capital_initial", 0)
        self.create_summary_card(summary_frame, "📊 TOTAL VALUE", "portfolio_value", 1)
        self.create_summary_card(summary_frame, "💵 AVAILABLE CASH", "available_cash", 2)
        self.create_summary_card(summary_frame, "📈 TOTAL PROFIT/LOSS", "total_pnl", 3)
        self.create_summary_card(summary_frame, "📊 RETURN %", "return_pct", 4)
        self.create_summary_card(summary_frame, "🎯 WIN RATE", "win_rate", 5)

    def create_summary_card(self, parent, title, key, column):
        """Create a summary card"""
        card = tk.Frame(parent, bg='#3d3d3d', relief=tk.RAISED, borderwidth=2)
        card.grid(row=0, column=column, padx=5, pady=5, sticky='ew')
        parent.columnconfigure(column, weight=1)

        title_label = tk.Label(
            card,
            text=title,
            font=('Arial', 10, 'bold'),
            bg='#3d3d3d',
            fg='#888888'
        )
        title_label.pack(pady=(10, 5))

        value_label = tk.Label(
            card,
            text="₹0",
            font=('Arial', 16, 'bold'),
            bg='#3d3d3d',
            fg='#ffffff'
        )
        value_label.pack(pady=(0, 10))

        # Store reference
        setattr(self, f"label_{key}", value_label)

    def create_swing_tab(self):
        """Create swing trading tab"""
        swing_frame = ttk.Frame(self.notebook)
        self.notebook.add(swing_frame, text='🔥 SWING TRADES')

        # Table
        self.swing_tree = self.create_positions_table(swing_frame)

    def create_positional_tab(self):
        """Create positional trading tab"""
        pos_frame = ttk.Frame(self.notebook)
        self.notebook.add(pos_frame, text='📈 POSITIONAL TRADES')

        # Table
        self.positional_tree = self.create_positions_table(pos_frame)

    def create_positions_table(self, parent):
        """Create positions table"""
        # Frame for table
        table_frame = tk.Frame(parent, bg='#1e1e1e')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview
        columns = (
            'Symbol', 'Shares', 'Entry Price', 'Current Price',
            'Invested', 'Current Value', 'P&L', 'P&L %',
            'Stop Loss', 'Target', 'Days Held', 'Max Days'
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=15
        )

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Column headings
        for col in columns:
            tree.heading(col, text=col)
            if col in ['Symbol']:
                tree.column(col, width=100)
            elif col in ['Shares', 'Days Held', 'Max Days']:
                tree.column(col, width=80)
            elif col in ['P&L %']:
                tree.column(col, width=80)
            else:
                tree.column(col, width=110)

        # Grid layout
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        return tree

    def create_logs_tab(self):
        """Create trade logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text='📜 TRADE LOGS')

        # Filters
        filter_frame = tk.Frame(logs_frame, bg='#2d2d2d')
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            filter_frame,
            text="Filter:",
            font=('Arial', 10, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        ).pack(side=tk.LEFT, padx=5)

        self.log_filter = ttk.Combobox(
            filter_frame,
            values=['All Trades', 'Swing Only', 'Positional Only', 'Winners', 'Losers'],
            state='readonly',
            width=20
        )
        self.log_filter.set('All Trades')
        self.log_filter.pack(side=tk.LEFT, padx=5)
        self.log_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_logs())

        # Refresh button
        tk.Button(
            filter_frame,
            text="🔄 Refresh Logs",
            command=self.refresh_logs,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=10)

        # Table for logs
        self.logs_tree = self.create_logs_table(logs_frame)

    def create_logs_table(self, parent):
        """Create trade logs table"""
        table_frame = tk.Frame(parent, bg='#1e1e1e')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        columns = (
            'Date', 'Symbol', 'Strategy', 'Shares',
            'Entry', 'Exit', 'P&L', 'P&L %',
            'Reason', 'Duration'
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=20
        )

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        for col in columns:
            tree.heading(col, text=col)
            if col in ['Date', 'Duration', 'Reason']:
                tree.column(col, width=120)
            elif col in ['Symbol', 'Strategy']:
                tree.column(col, width=100)
            elif col in ['Shares']:
                tree.column(col, width=80)
            else:
                tree.column(col, width=100)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        return tree

    def create_control_panel(self):
        """Create control panel with buttons"""
        control_frame = tk.Frame(self.root, bg='#2d2d2d', height=60)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Refresh button
        tk.Button(
            control_frame,
            text="🔄 Refresh Now",
            command=self.refresh_data,
            bg='#2196F3',
            fg='white',
            font=('Arial', 12, 'bold'),
            cursor='hand2',
            width=15
        ).pack(side=tk.LEFT, padx=10)

        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            control_frame,
            text="Auto-refresh (5s)",
            variable=self.auto_refresh_var,
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#ffffff',
            selectcolor='#1e1e1e',
            command=self.toggle_auto_refresh
        ).pack(side=tk.LEFT, padx=10)

        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="Last updated: Never",
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#888888'
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def load_portfolio_data(self, portfolio_file: str) -> Dict:
        """Load portfolio data from file"""
        if not os.path.exists(portfolio_file):
            return {
                'capital': 0,
                'positions': {},
                'performance': {'total_pnl': 0, 'total_trades': 0}
            }

        try:
            with open(portfolio_file, 'r') as f:
                return json.load(f)
        except:
            return {
                'capital': 0,
                'positions': {},
                'performance': {'total_pnl': 0, 'total_trades': 0}
            }

    def load_trade_history(self, trades_file: str) -> List[Dict]:
        """Load trade history from file"""
        if not os.path.exists(trades_file):
            return []

        try:
            with open(trades_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def refresh_data(self):
        """Refresh all data"""
        # Load portfolio data
        swing_portfolio = self.load_portfolio_data(self.swing_portfolio_file)
        pos_portfolio = self.load_portfolio_data(self.positional_portfolio_file)

        # Calculate totals
        swing_capital = swing_portfolio.get('capital', 0)
        pos_capital = pos_portfolio.get('capital', 0)
        total_cash = swing_capital + pos_capital

        swing_positions = swing_portfolio.get('positions', {})
        pos_positions = pos_portfolio.get('positions', {})

        # Calculate invested and portfolio value
        swing_invested = sum(pos['cost'] for pos in swing_positions.values())
        pos_invested = sum(pos['cost'] for pos in pos_positions.values())
        total_invested = swing_invested + pos_invested

        # Get current prices and calculate current value
        # For now, use cost as approximation (in real system, fetch live prices)
        swing_value = swing_invested
        pos_value = pos_invested
        total_current_value = swing_value + pos_value

        total_portfolio_value = total_cash + total_current_value

        # Initial capital (hardcoded for now, should be stored)
        initial_capital = 100000

        # Total P&L
        total_pnl = total_portfolio_value - initial_capital
        return_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0

        # Win rate
        swing_trades = self.load_trade_history(self.swing_trades_file)
        pos_trades = self.load_trade_history(self.positional_trades_file)
        all_trades = swing_trades + pos_trades

        total_trades = len(all_trades)
        winning_trades = sum(1 for t in all_trades if t.get('pnl', 0) > 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Update summary labels
        self.label_capital_initial.config(text=f"₹{initial_capital:,.0f}")
        self.label_portfolio_value.config(text=f"₹{total_portfolio_value:,.0f}")
        self.label_available_cash.config(text=f"₹{total_cash:,.0f}")

        # Color P&L
        pnl_color = '#00ff00' if total_pnl >= 0 else '#ff0000'
        self.label_total_pnl.config(text=f"₹{total_pnl:+,.0f}", fg=pnl_color)
        self.label_return_pct.config(text=f"{return_pct:+.2f}%", fg=pnl_color)
        self.label_win_rate.config(text=f"{win_rate:.1f}%")

        # Update positions tables
        self.update_positions_table(self.swing_tree, swing_positions, 'swing')
        self.update_positions_table(self.positional_tree, pos_positions, 'positional')

        # Update status
        self.status_label.config(text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    def update_positions_table(self, tree, positions: Dict, strategy: str):
        """Update positions table"""
        # Clear existing
        for item in tree.get_children():
            tree.delete(item)

        # Add positions
        for symbol, pos in positions.items():
            shares = pos.get('shares', 0)
            entry_price = pos.get('entry_price', 0)
            current_price = entry_price  # TODO: Fetch live price

            invested = pos.get('cost', 0)
            current_value = shares * current_price
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0

            stop_loss = pos.get('stop_loss', 0)
            target = pos.get('target2', 0)

            # Calculate days held
            entry_date_str = pos.get('entry_date', '')
            try:
                entry_date = datetime.fromisoformat(entry_date_str)
                days_held = (datetime.now() - entry_date).days
            except:
                days_held = 0

            max_days = pos.get('max_holding_days', 30)

            # Color P&L
            pnl_display = f"₹{pnl:+,.0f}"
            pnl_pct_display = f"{pnl_pct:+.2f}%"

            values = (
                symbol,
                shares,
                f"₹{entry_price:.2f}",
                f"₹{current_price:.2f}",
                f"₹{invested:,.0f}",
                f"₹{current_value:,.0f}",
                pnl_display,
                pnl_pct_display,
                f"₹{stop_loss:.2f}",
                f"₹{target:.2f}",
                days_held,
                max_days
            )

            tag = 'profit' if pnl >= 0 else 'loss'
            tree.insert('', 'end', values=values, tags=(tag,))

        # Configure tags
        tree.tag_configure('profit', foreground='#00ff00')
        tree.tag_configure('loss', foreground='#ff0000')

    def refresh_logs(self):
        """Refresh trade logs"""
        # Clear existing
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)

        # Load trades
        swing_trades = self.load_trade_history(self.swing_trades_file)
        pos_trades = self.load_trade_history(self.positional_trades_file)

        # Tag trades with strategy
        for trade in swing_trades:
            trade['strategy'] = 'Swing'
        for trade in pos_trades:
            trade['strategy'] = 'Positional'

        all_trades = swing_trades + pos_trades

        # Filter
        filter_value = self.log_filter.get()
        if filter_value == 'Swing Only':
            all_trades = [t for t in all_trades if t.get('strategy') == 'Swing']
        elif filter_value == 'Positional Only':
            all_trades = [t for t in all_trades if t.get('strategy') == 'Positional']
        elif filter_value == 'Winners':
            all_trades = [t for t in all_trades if t.get('pnl', 0) > 0]
        elif filter_value == 'Losers':
            all_trades = [t for t in all_trades if t.get('pnl', 0) < 0]

        # Sort by date (latest first)
        all_trades.sort(key=lambda x: x.get('exit_date', ''), reverse=True)

        # Add to table
        for trade in all_trades:
            exit_date = trade.get('exit_date', '')
            try:
                date_display = datetime.fromisoformat(exit_date).strftime('%Y-%m-%d %H:%M')
            except:
                date_display = exit_date[:16] if exit_date else 'N/A'

            symbol = trade.get('symbol', 'N/A')
            strategy = trade.get('strategy', 'N/A')
            shares = trade.get('shares', 0)
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            pnl = trade.get('pnl', 0)
            pnl_pct = trade.get('pnl_percent', 0)
            reason = trade.get('reason', 'N/A')

            # Calculate duration
            try:
                entry_date = datetime.fromisoformat(trade.get('entry_date', ''))
                exit_date_dt = datetime.fromisoformat(exit_date)
                duration = (exit_date_dt - entry_date).days
                duration_display = f"{duration} days"
            except:
                duration_display = 'N/A'

            values = (
                date_display,
                symbol,
                strategy,
                shares,
                f"₹{entry_price:.2f}",
                f"₹{exit_price:.2f}",
                f"₹{pnl:+,.0f}",
                f"{pnl_pct:+.2f}%",
                reason,
                duration_display
            )

            tag = 'profit' if pnl >= 0 else 'loss'
            self.logs_tree.insert('', 'end', values=values, tags=(tag,))

        # Configure tags
        self.logs_tree.tag_configure('profit', foreground='#00ff00')
        self.logs_tree.tag_configure('loss', foreground='#ff0000')

    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        self.auto_refresh = self.auto_refresh_var.get()

    def auto_refresh_data(self):
        """Auto-refresh data periodically"""
        if self.auto_refresh:
            self.refresh_data()

        # Schedule next refresh
        self.root.after(self.refresh_interval, self.auto_refresh_data)


def main():
    """Launch the GUI"""
    root = tk.Tk()
    app = TradingDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
