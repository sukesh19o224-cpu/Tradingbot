"""
🧪 MINI TEST - Top 500 Stocks
Quick test with Discord alerts
"""

import time
from datetime import datetime

# Local imports
from config.settings import *
from config.nse_top_500_live import NSE_TOP_500
from src.data.sequential_scanner import SequentialScanner
from src.alerts.discord_alerts import DiscordAlerts

class MiniTest:
    """Mini test scanner - Top 500 stocks with Discord alerts"""

    def __init__(self, stock_count=500, enable_discord=True):
        print("\n" + "="*80)
        print(f"🧪 MINI TEST - Top {stock_count} NSE Stocks")
        print("="*80)
        print(f"📊 Scanning: Top {stock_count} stocks (market cap ranked)")
        print(f"📱 Discord Alerts: {'YES' if enable_discord else 'NO (disabled for optimization)'}")
        print("💰 Auto-buying: NO (test mode)")
        print("📁 Portfolio: NO (test mode)")
        print("="*80 + "\n")

        self.scanner = SequentialScanner(api_delay=0.3)
        self.discord = DiscordAlerts() if enable_discord else None
        self.enable_discord = enable_discord

        # Get top N stocks
        self.stocks = NSE_TOP_500[:stock_count]

        print(f"✅ Mini test initialized")
        print(f"📊 Total stocks: {len(self.stocks)}")
        print(f"🐌 Sequential scanning: One by one (safe)")
        print(f"⏱️ API delay: 0.3s between stocks")

        if self.enable_discord and self.discord:
            print(f"📱 Discord: {'Enabled' if self.discord.enabled else 'Disabled - Set DISCORD_WEBHOOK_URL in .env'}")
            if not self.discord.enabled:
                print("\n⚠️  WARNING: Discord is disabled!")
                print("   Set DISCORD_WEBHOOK_URL in your .env file to enable alerts")
        else:
            print(f"📱 Discord: Disabled (for optimization)")

        print("\n")

    def run(self):
        """Run mini test scan"""

        print(f"\n{'='*80}")
        print(f"🚀 STARTING MINI TEST @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        start_time = time.time()

        # Scan top 100 stocks
        print(f"📊 Scanning {len(self.stocks)} stocks sequentially...")
        result = self.scanner.scan_all_stocks(self.stocks)

        scan_time = time.time() - start_time

        # Get signals
        swing_signals = result.get('swing_signals', [])
        positional_signals = result.get('positional_signals', [])
        total_signals = len(swing_signals) + len(positional_signals)

        print(f"\n✅ Scan complete in {scan_time:.1f} seconds")
        print(f"📊 Found {total_signals} opportunities")
        print(f"   🔥 Swing: {len(swing_signals)}")
        print(f"   📈 Positional: {len(positional_signals)}\n")

        if total_signals == 0:
            print("❌ No opportunities found in this scan")
            return

        # Display top signals
        print(f"\n{'='*80}")
        print(f"🏆 TOP SIGNALS")
        print(f"{'='*80}")

        if swing_signals:
            print(f"\n🔥 SWING SIGNALS ({len(swing_signals)}):")
            for i, sig in enumerate(swing_signals[:10], 1):
                print(f"{i}. {sig['symbol']:<12} | Score: {sig.get('score', 0):.1f} | "
                      f"Entry: ₹{sig.get('entry_price', 0):.2f} | "
                      f"SL: ₹{sig.get('stop_loss', 0):.2f}")

        if positional_signals:
            print(f"\n📈 POSITIONAL SIGNALS ({len(positional_signals)}):")
            for i, sig in enumerate(positional_signals[:10], 1):
                print(f"{i}. {sig['symbol']:<12} | Score: {sig.get('score', 0):.1f} | "
                      f"Entry: ₹{sig.get('entry_price', 0):.2f} | "
                      f"SL: ₹{sig.get('stop_loss', 0):.2f}")

        print(f"{'='*80}\n")

        # Send Discord alerts
        if self.enable_discord and self.discord and self.discord.enabled:
            print(f"📱 Sending Discord alerts...")

            # Send swing signals
            for sig in swing_signals:
                self.discord.send_swing_signal(sig)
                time.sleep(0.5)

            # Send positional signals
            for sig in positional_signals:
                self.discord.send_positional_signal(sig)
                time.sleep(0.5)

            print(f"✅ Discord alerts sent!")
        else:
            print(f"⚠️  Discord disabled - no alerts sent")

        print(f"\n{'='*80}")
        print(f"✅ MINI TEST COMPLETE")
        print(f"{'='*80}")
        print(f"📊 Total signals: {total_signals}")
        print(f"   🔥 Swing: {len(swing_signals)}")
        print(f"   📈 Positional: {len(positional_signals)}")
        print(f"⏱️  Scan time: {scan_time:.1f} seconds")
        print(f"📱 Discord alerts: {total_signals if (self.enable_discord and self.discord and self.discord.enabled) else 0}")
        print(f"{'='*80}\n")

        return result


if __name__ == "__main__":
    tester = MiniTest()
    tester.run()

    print("\n📌 NEXT STEPS:")
    print("   1. Check your Discord for BUY signals")
    print("   2. If everything looks good, run the full system:")
    print("      python main_eod_system.py --mode once")
    print("\n   Or run continuous mode:")
    print("      python main_eod_system.py --mode continuous")
    print("\n")
