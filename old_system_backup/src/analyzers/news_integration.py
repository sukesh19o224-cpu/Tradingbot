"""
NEWS INTEGRATION - Connects News Sentinel to Main Trading System

Adds news awareness to:
1. Position monitoring (exit on negative news)
2. Entry validation (avoid stocks with bad news)
3. Market regime (overall sentiment)
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analyzers.news_sentinel import NewsSentinel


class NewsIntegration:
    """
    Integrates news sentiment into trading decisions
    """
    
    def __init__(self, enable_news_checks=True):
        self.enable_news_checks = enable_news_checks
        
        if enable_news_checks:
            self.sentinel = NewsSentinel()
            print("✅ News Integration: ENABLED")
        else:
            self.sentinel = None
            print("⚠️ News Integration: DISABLED")
    
    def check_before_entry(self, symbol):
        """
        Check news before entering a position
        Returns: (allowed: bool, reason: str, sentiment_score: float)
        """
        if not self.enable_news_checks:
            return True, "News checks disabled", 0
        
        result = self.sentinel.check_stock_news(symbol, hours_back=12)
        
        # Block on critical news
        if result['has_critical']:
            return False, f"🚨 CRITICAL NEWS - Entry blocked", result['sentiment_score']
        
        # Block on strong negative sentiment
        if result['sentiment_score'] <= -5:
            return False, f"❌ Negative news (score: {result['sentiment_score']:.1f}) - Entry blocked", result['sentiment_score']
        
        # Warn on moderate negative
        if result['sentiment_score'] <= -3:
            return True, f"⚠️ Slightly negative news (score: {result['sentiment_score']:.1f}) - Proceed with caution", result['sentiment_score']
        
        # All clear
        if result['news_count'] > 0:
            return True, f"✅ News sentiment OK (score: {result['sentiment_score']:+.1f})", result['sentiment_score']
        else:
            return True, "ℹ️ No recent news found", 0
    
    def check_during_hold(self, symbol, current_profit_pct=0):
        """
        Check news while holding a position
        Returns: (should_exit: bool, reason: str)
        """
        if not self.enable_news_checks:
            return False, "News checks disabled"
        
        result = self.sentinel.check_stock_news(symbol, hours_back=6)
        
        # Exit immediately on critical news
        if result['has_critical']:
            return True, f"🚨 CRITICAL NEWS ALERT - Exit immediately (current P&L: {current_profit_pct:+.1f}%)"
        
        # Exit on strong negative if profitable
        if result['sentiment_score'] <= -5 and current_profit_pct > 2:
            return True, f"❌ Negative news + profitable ({current_profit_pct:+.1f}%) - Secure gains"
        
        # Exit on strong negative if losing badly
        if result['sentiment_score'] <= -5 and current_profit_pct < -4:
            return True, f"❌ Negative news + big loss ({current_profit_pct:+.1f}%) - Cut losses"
        
        # No action needed
        return False, "News sentiment acceptable"
    
    def get_market_news_sentiment(self):
        """
        Get overall market sentiment
        Returns: (score: float, mood: str, should_trade: bool)
        """
        if not self.enable_news_checks:
            return 0, "UNKNOWN", True
        
        result = self.sentinel.get_market_sentiment()
        
        score = result['score']
        mood = result['mood']
        
        # Don't trade if extremely bearish
        should_trade = score > -5
        
        return score, mood, should_trade
    
    def scan_watchlist_for_news_catalysts(self, watchlist_symbols):
        """
        Find stocks with positive news catalysts
        Returns: list of symbols with good news
        """
        if not self.enable_news_checks:
            return []
        
        print("\n📰 Scanning watchlist for news catalysts...")
        
        opportunities = self.sentinel.check_watchlist_news(watchlist_symbols)
        
        if opportunities:
            print(f"\n✅ Found {len(opportunities)} stocks with positive news:")
            for opp in opportunities:
                print(f"   {opp['symbol']}: {opp['reason']} (sentiment: {opp['sentiment']:+.1f})")
        else:
            print("   No significant news catalysts found")
        
        return [opp['symbol'] for opp in opportunities]
    
    def generate_news_report(self, positions):
        """
        Generate comprehensive news report for portfolio
        Returns: dict with alerts and recommendations
        """
        if not self.enable_news_checks:
            return {
                'enabled': False,
                'alerts': [],
                'recommendations': []
            }
        
        print("\n📰 Generating news report for portfolio...")
        
        alerts = self.sentinel.check_portfolio_news(positions)
        
        # Categorize alerts
        critical_alerts = [a for a in alerts if a['type'] == 'CRITICAL']
        negative_alerts = [a for a in alerts if a['type'] == 'NEGATIVE']
        positive_alerts = [a for a in alerts if a['type'] == 'POSITIVE']
        
        # Generate recommendations
        recommendations = []
        
        for alert in critical_alerts:
            recommendations.append({
                'symbol': alert['symbol'],
                'action': 'EXIT_IMMEDIATELY',
                'priority': 'CRITICAL',
                'reason': alert['message']
            })
        
        for alert in negative_alerts:
            recommendations.append({
                'symbol': alert['symbol'],
                'action': 'MONITOR_CLOSELY',
                'priority': 'HIGH',
                'reason': alert['message']
            })
        
        report = {
            'enabled': True,
            'total_alerts': len(alerts),
            'critical': len(critical_alerts),
            'negative': len(negative_alerts),
            'positive': len(positive_alerts),
            'alerts': alerts,
            'recommendations': recommendations
        }
        
        # Display summary
        if critical_alerts:
            print(f"\n🚨 CRITICAL: {len(critical_alerts)} position(s) need immediate attention!")
        if negative_alerts:
            print(f"⚠️ WARNING: {len(negative_alerts)} position(s) have negative news")
        if positive_alerts:
            print(f"✅ POSITIVE: {len(positive_alerts)} position(s) have good news")
        
        return report


# Utility functions for easy integration

def should_enter(symbol, enable_news=True):
    """Quick check: Should we enter this stock?"""
    integration = NewsIntegration(enable_news_checks=enable_news)
    allowed, reason, score = integration.check_before_entry(symbol)
    print(f"\n{symbol}: {reason}")
    return allowed

def should_exit(symbol, current_profit=0, enable_news=True):
    """Quick check: Should we exit based on news?"""
    integration = NewsIntegration(enable_news_checks=enable_news)
    exit_now, reason = integration.check_during_hold(symbol, current_profit)
    print(f"\n{symbol}: {reason}")
    return exit_now


if __name__ == "__main__":
    """
    Test the integration
    """
    
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║        📰 NEWS INTEGRATION - Test Mode                 ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    integration = NewsIntegration(enable_news_checks=True)
    
    # Test 1: Check market sentiment
    print("\n" + "="*70)
    print("TEST 1: Market News Sentiment")
    print("="*70)
    
    score, mood, should_trade = integration.get_market_news_sentiment()
    print(f"\nMarket Mood: {mood}")
    print(f"Sentiment Score: {score:+.1f}")
    print(f"Should Trade: {'✅ YES' if should_trade else '❌ NO'}")
    
    # Test 2: Entry validation
    print("\n" + "="*70)
    print("TEST 2: Entry Validation")
    print("="*70)
    
    test_stocks = ['RELIANCE', 'TATAMOTORS', 'HDFCBANK']
    
    for stock in test_stocks:
        allowed, reason, sentiment = integration.check_before_entry(stock)
        print(f"\n{stock}:")
        print(f"   Entry Allowed: {'✅ YES' if allowed else '❌ NO'}")
        print(f"   Reason: {reason}")
        print(f"   Sentiment: {sentiment:+.1f}")
    
    # Test 3: Hold validation (simulate)
    print("\n" + "="*70)
    print("TEST 3: Hold Validation")
    print("="*70)
    
    # Simulate checking a profitable position
    should_exit, reason = integration.check_during_hold('RELIANCE', current_profit_pct=5)
    print(f"\nRELIANCE (currently +5% profit):")
    print(f"   Should Exit: {'✅ YES' if should_exit else '❌ NO'}")
    print(f"   Reason: {reason}")
    
    # Test 4: Portfolio report (simulated)
    print("\n" + "="*70)
    print("TEST 4: Portfolio News Report")
    print("="*70)
    
    mock_positions = [
        {'symbol': 'RELIANCE'},
        {'symbol': 'TATAMOTORS'},
        {'symbol': 'HDFCBANK'}
    ]
    
    report = integration.generate_news_report(mock_positions)
    
    if report['enabled']:
        print(f"\n📊 Report Summary:")
        print(f"   Total Alerts: {report['total_alerts']}")
        print(f"   Critical: {report['critical']}")
        print(f"   Negative: {report['negative']}")
        print(f"   Positive: {report['positive']}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   {rec['priority']}: {rec['symbol']} - {rec['action']}")
    
    print("\n" + "="*70)
    print("✅ Integration Test Complete!")
    print("="*70)