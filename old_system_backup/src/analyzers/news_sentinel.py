"""
NEWS SENTINEL - Free News Sentiment Analyzer
Tracks news for stocks in portfolio and watchlist
100% FREE - Uses RSS feeds and basic NLP

Features:
- Scrapes Economic Times, MoneyControl, Business Standard
- Detects positive/negative news
- Alerts on major events (earnings, regulatory, management)
- Stock-specific news tracking
- Zero cost APIs
"""

import feedparser
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from collections import defaultdict
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class NewsSentinel:
    """
    Monitors news sentiment for stocks
    100% FREE solution using RSS feeds
    """
    
    def __init__(self):
        print("📰 News Sentinel Initializing...")
        
        # RSS Feed sources (all FREE)
        self.news_sources = {
            'economic_times': 'https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms',
            'moneycontrol': 'https://www.moneycontrol.com/rss/marketoutlook.xml',
            'business_standard': 'https://www.business-standard.com/rss/markets-106.rss',
            'livemint': 'https://www.livemint.com/rss/markets',
        }
        
        # Sentiment keywords (basic NLP)
        self.positive_keywords = [
            'surge', 'rally', 'gain', 'profit', 'beat', 'upgrade', 'bullish',
            'record', 'high', 'breakout', 'strong', 'growth', 'up', 'rise',
            'jump', 'soar', 'outperform', 'positive', 'boost', 'momentum',
            'buy', 'recommend', 'acquisition', 'contract', 'order', 'expansion'
        ]
        
        self.negative_keywords = [
            'fall', 'drop', 'loss', 'miss', 'downgrade', 'bearish', 'crash',
            'decline', 'low', 'breakdown', 'weak', 'concern', 'down', 'plunge',
            'slump', 'underperform', 'negative', 'sell', 'warning', 'investigation',
            'fraud', 'penalty', 'lawsuit', 'debt', 'bankruptcy', 'layoff'
        ]
        
        self.critical_keywords = [
            'sebi', 'raid', 'probe', 'scam', 'fraud', 'arrest', 'investigation',
            'penalty', 'ban', 'suspension', 'delisting', 'bankruptcy', 'default'
        ]
        
        # Cache to avoid duplicate alerts
        self.seen_headlines = set()
        self.last_check = {}
        
        print("✅ News Sentinel Ready!")
        print(f"   Monitoring {len(self.news_sources)} sources")
        print(f"   Tracking {len(self.positive_keywords)} positive keywords")
        print(f"   Tracking {len(self.negative_keywords)} negative keywords")
    
    def check_stock_news(self, symbol, hours_back=24):
        """
        Check news for a specific stock
        Returns: (sentiment_score, news_items)
        """
        print(f"\n🔍 Checking news for {symbol}...")
        
        # Normalize symbol
        symbol_clean = symbol.upper().replace('.NS', '')
        
        # Search variations
        search_terms = [
            symbol_clean,
            symbol_clean.lower(),
        ]
        
        all_news = []
        
        # Check each news source
        for source_name, feed_url in self.news_sources.items():
            try:
                print(f"   📡 Fetching from {source_name}...", end=' ')
                
                feed = feedparser.parse(feed_url)
                
                if not feed.entries:
                    print("⚠️ No entries")
                    continue
                
                print(f"✅ {len(feed.entries)} articles")
                
                # Filter for relevant articles
                for entry in feed.entries:
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    link = entry.get('link', '')
                    published = entry.get('published', '')
                    
                    # Check if article mentions the stock
                    full_text = f"{title} {summary}".upper()
                    
                    is_relevant = any(term in full_text for term in search_terms)
                    
                    if is_relevant:
                        # Parse date
                        try:
                            pub_date = datetime(*entry.published_parsed[:6])
                            hours_ago = (datetime.now() - pub_date).total_seconds() / 3600
                            
                            if hours_ago > hours_back:
                                continue
                        except:
                            hours_ago = 0
                        
                        # Analyze sentiment
                        sentiment = self._analyze_sentiment(title, summary)
                        
                        news_item = {
                            'source': source_name,
                            'title': title,
                            'summary': summary[:200],
                            'link': link,
                            'published': published,
                            'hours_ago': round(hours_ago, 1),
                            'sentiment': sentiment['score'],
                            'sentiment_label': sentiment['label'],
                            'is_critical': sentiment['is_critical']
                        }
                        
                        all_news.append(news_item)
                
                time.sleep(0.5)  # Polite delay
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Calculate overall sentiment
        if all_news:
            avg_sentiment = sum(item['sentiment'] for item in all_news) / len(all_news)
            
            # Check for critical news
            has_critical = any(item['is_critical'] for item in all_news)
            
            print(f"\n📊 Summary for {symbol}:")
            print(f"   Found {len(all_news)} relevant articles")
            print(f"   Average Sentiment: {avg_sentiment:+.1f}")
            
            if has_critical:
                print(f"   🚨 CRITICAL NEWS DETECTED!")
            
            return {
                'symbol': symbol,
                'news_count': len(all_news),
                'sentiment_score': avg_sentiment,
                'has_critical': has_critical,
                'news_items': sorted(all_news, key=lambda x: x['hours_ago'])
            }
        else:
            print(f"   ℹ️ No recent news found for {symbol}")
            return {
                'symbol': symbol,
                'news_count': 0,
                'sentiment_score': 0,
                'has_critical': False,
                'news_items': []
            }
    
    def _analyze_sentiment(self, title, summary):
        """
        Analyze sentiment using keyword matching
        Returns: {'score': float, 'label': str, 'is_critical': bool}
        """
        text = f"{title} {summary}".lower()
        
        # Count keywords
        positive_count = sum(1 for word in self.positive_keywords if word in text)
        negative_count = sum(1 for word in self.negative_keywords if word in text)
        critical_count = sum(1 for word in self.critical_keywords if word in text)
        
        # Calculate score (-10 to +10)
        score = (positive_count * 2) - (negative_count * 2) - (critical_count * 5)
        score = max(min(score, 10), -10)  # Clamp to range
        
        # Label
        if critical_count > 0:
            label = "🚨 CRITICAL"
        elif score >= 3:
            label = "✅ POSITIVE"
        elif score <= -3:
            label = "❌ NEGATIVE"
        else:
            label = "➖ NEUTRAL"
        
        return {
            'score': score,
            'label': label,
            'is_critical': critical_count > 0
        }
    
    def check_portfolio_news(self, positions):
        """
        Check news for all positions in portfolio
        Returns: dict with alerts
        """
        print(f"\n{'='*70}")
        print("📰 CHECKING NEWS FOR PORTFOLIO")
        print(f"{'='*70}")
        
        alerts = []
        
        for position in positions:
            symbol = position.get('symbol', '').replace('.NS', '')
            
            result = self.check_stock_news(symbol, hours_back=24)
            
            # Generate alerts
            if result['has_critical']:
                alerts.append({
                    'type': 'CRITICAL',
                    'symbol': symbol,
                    'message': f"🚨 CRITICAL NEWS for {symbol}! Immediate review required.",
                    'sentiment': result['sentiment_score'],
                    'news_count': result['news_count'],
                    'action': 'CONSIDER_EXIT'
                })
            
            elif result['sentiment_score'] <= -5:
                alerts.append({
                    'type': 'NEGATIVE',
                    'symbol': symbol,
                    'message': f"❌ Negative news for {symbol}. Monitor closely.",
                    'sentiment': result['sentiment_score'],
                    'news_count': result['news_count'],
                    'action': 'MONITOR'
                })
            
            elif result['sentiment_score'] >= 5:
                alerts.append({
                    'type': 'POSITIVE',
                    'symbol': symbol,
                    'message': f"✅ Positive news for {symbol}. Good momentum.",
                    'sentiment': result['sentiment_score'],
                    'news_count': result['news_count'],
                    'action': 'HOLD'
                })
            
            time.sleep(1)  # Polite delay between stocks
        
        return alerts
    
    def check_watchlist_news(self, symbols):
        """
        Check news for watchlist stocks
        Identifies sudden breakout opportunities
        """
        print(f"\n{'='*70}")
        print("📰 CHECKING NEWS FOR WATCHLIST")
        print(f"{'='*70}")
        
        opportunities = []
        
        for symbol in symbols:
            symbol_clean = symbol.replace('.NS', '')
            
            result = self.check_stock_news(symbol_clean, hours_back=6)  # Only last 6 hours
            
            # Look for positive catalysts
            if result['sentiment_score'] >= 5 and result['news_count'] >= 2:
                opportunities.append({
                    'symbol': symbol_clean,
                    'sentiment': result['sentiment_score'],
                    'news_count': result['news_count'],
                    'reason': 'Positive news catalyst',
                    'latest_headlines': [item['title'] for item in result['news_items'][:3]]
                })
            
            time.sleep(0.5)
        
        return opportunities
    
    def get_market_sentiment(self):
        """
        Get overall market sentiment from headlines
        Returns: overall score and trending topics
        """
        print(f"\n{'='*70}")
        print("📊 CHECKING OVERALL MARKET SENTIMENT")
        print(f"{'='*70}")
        
        all_headlines = []
        
        for source_name, feed_url in self.news_sources.items():
            try:
                print(f"   📡 Fetching from {source_name}...", end=' ')
                
                feed = feedparser.parse(feed_url)
                
                if feed.entries:
                    # Get last 10 headlines
                    for entry in feed.entries[:10]:
                        title = entry.get('title', '')
                        all_headlines.append(title)
                    
                    print(f"✅ {len(feed.entries[:10])} headlines")
                else:
                    print("⚠️ No entries")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Analyze overall sentiment
        if all_headlines:
            sentiments = [self._analyze_sentiment(h, '')['score'] for h in all_headlines]
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Categorize
            if avg_sentiment >= 2:
                mood = "🟢 BULLISH"
                advice = "Good environment for long positions"
            elif avg_sentiment <= -2:
                mood = "🔴 BEARISH"
                advice = "Caution: Consider reducing exposure"
            else:
                mood = "🟡 NEUTRAL"
                advice = "Mixed signals, selective trading"
            
            print(f"\n📊 Market Sentiment Analysis:")
            print(f"   Headlines analyzed: {len(all_headlines)}")
            print(f"   Average score: {avg_sentiment:+.1f}")
            print(f"   Overall mood: {mood}")
            print(f"   Advice: {advice}")
            
            return {
                'score': avg_sentiment,
                'mood': mood,
                'advice': advice,
                'headlines_count': len(all_headlines)
            }
        else:
            return {
                'score': 0,
                'mood': "❓ UNKNOWN",
                'advice': "Could not fetch market news",
                'headlines_count': 0
            }
    
    def display_news_report(self, symbol):
        """
        Display formatted news report for a stock
        """
        result = self.check_stock_news(symbol, hours_back=48)
        
        print(f"\n{'='*70}")
        print(f"📰 NEWS REPORT: {symbol}")
        print(f"{'='*70}")
        
        if result['news_count'] == 0:
            print("ℹ️ No recent news found")
            return
        
        print(f"\n📊 Summary:")
        print(f"   Articles found: {result['news_count']}")
        print(f"   Sentiment score: {result['sentiment_score']:+.1f}")
        
        if result['has_critical']:
            print(f"   ⚠️ CRITICAL NEWS DETECTED!")
        
        print(f"\n📋 Recent Headlines:")
        print(f"{'─'*70}")
        
        for i, item in enumerate(result['news_items'][:5], 1):
            print(f"\n{i}. {item['sentiment_label']} | {item['hours_ago']}h ago | {item['source']}")
            print(f"   {item['title']}")
            if item.get('summary'):
                print(f"   {item['summary'][:150]}...")
            print(f"   🔗 {item['link']}")
        
        print(f"\n{'='*70}")
    
    def should_exit_position(self, symbol, current_profit_pct=0):
        """
        Decision helper: Should we exit based on news?
        """
        result = self.check_stock_news(symbol, hours_back=12)
        
        # Critical news = immediate exit
        if result['has_critical']:
            return True, "CRITICAL news detected - exit immediately"
        
        # Strong negative + in profit = take profit and exit
        if result['sentiment_score'] <= -5 and current_profit_pct > 3:
            return True, "Negative news + profitable - secure gains"
        
        # Strong negative + in loss = depends on size
        if result['sentiment_score'] <= -5 and current_profit_pct < -3:
            return True, "Negative news + losing - cut losses"
        
        # Otherwise hold
        return False, "No concerning news"
    
    def should_enter_position(self, symbol):
        """
        Decision helper: Is news sentiment favorable for entry?
        """
        result = self.check_stock_news(symbol, hours_back=6)
        
        # Critical news = don't enter
        if result['has_critical']:
            return False, "CRITICAL news - avoid entry"
        
        # Strong negative = don't enter
        if result['sentiment_score'] <= -3:
            return False, "Negative news sentiment - avoid"
        
        # No news or positive = OK to enter
        if result['sentiment_score'] >= 0:
            return True, "News sentiment favorable or neutral"
        
        return True, "Proceed with caution"


# Standalone function for quick checks
def quick_check(symbol):
    """Quick news check for any stock"""
    sentinel = NewsSentinel()
    sentinel.display_news_report(symbol)


if __name__ == "__main__":
    """
    Test the News Sentinel
    """
    
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║           📰 NEWS SENTINEL - Test Mode                 ║
    ║                                                        ║
    ║  Free news sentiment analyzer for Indian stocks       ║
    ║  Sources: ET, MoneyControl, BS, LiveMint              ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    sentinel = NewsSentinel()
    
    # Test 1: Check market sentiment
    print("\n" + "="*70)
    print("TEST 1: Overall Market Sentiment")
    print("="*70)
    
    market_sentiment = sentinel.get_market_sentiment()
    
    # Test 2: Check specific stocks
    test_stocks = ['RELIANCE', 'TCS', 'TATAMOTORS']
    
    print("\n" + "="*70)
    print("TEST 2: Specific Stock News")
    print("="*70)
    
    for stock in test_stocks:
        sentinel.display_news_report(stock)
        time.sleep(2)
    
    # Test 3: Portfolio check (simulated)
    print("\n" + "="*70)
    print("TEST 3: Portfolio News Check")
    print("="*70)
    
    mock_portfolio = [
        {'symbol': 'RELIANCE'},
        {'symbol': 'TATAMOTORS'},
        {'symbol': 'HDFCBANK'}
    ]
    
    alerts = sentinel.check_portfolio_news(mock_portfolio)
    
    if alerts:
        print(f"\n🔔 ALERTS GENERATED: {len(alerts)}")
        for alert in alerts:
            print(f"\n{alert['type']}: {alert['symbol']}")
            print(f"   {alert['message']}")
            print(f"   Sentiment: {alert['sentiment']:+.1f}")
            print(f"   Action: {alert['action']}")
    else:
        print("\n✅ No alerts - all clear!")
    
    print("\n" + "="*70)
    print("✅ News Sentinel Test Complete!")
    print("="*70)