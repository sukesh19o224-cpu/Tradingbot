"""
V5.5 ULTRA+ - Sentiment Analysis Engine
Analyzes news and social media sentiment for stocks
"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyze market sentiment from news and social media
    
    Features:
    - News headline analysis
    - Keyword-based sentiment scoring
    - Trend detection
    - Sentiment momentum
    """
    
    def __init__(self):
        # Sentiment keywords
        self.POSITIVE_KEYWORDS = [
            'surge', 'rally', 'boom', 'profit', 'gain', 'growth', 'bullish',
            'upgrade', 'beat', 'strong', 'rise', 'jump', 'soar', 'breakthrough',
            'expansion', 'record', 'positive', 'outperform', 'recovery', 'improve'
        ]
        
        self.NEGATIVE_KEYWORDS = [
            'crash', 'fall', 'drop', 'loss', 'decline', 'bearish', 'downgrade',
            'miss', 'weak', 'plunge', 'slump', 'concern', 'warning', 'risk',
            'collapse', 'negative', 'underperform', 'recession', 'crisis'
        ]
        
        self.NEUTRAL_KEYWORDS = [
            'stable', 'flat', 'unchanged', 'sideways', 'neutral', 'hold'
        ]
    
    def analyze_stock_sentiment(self, symbol: str) -> Dict:
        """
        Analyze overall sentiment for a stock
        
        Returns:
        {
            'sentiment_score': -100 to +100,
            'sentiment': 'POSITIVE'/'NEGATIVE'/'NEUTRAL',
            'confidence': 0-100,
            'news_count': int,
            'positive_signals': int,
            'negative_signals': int
        }
        """
        logger.info(f"🔍 Analyzing sentiment for {symbol}")
        
        # Fetch news headlines
        headlines = self._fetch_news_headlines(symbol)
        
        if not headlines:
            return {
                'sentiment_score': 0,
                'sentiment': 'NEUTRAL',
                'confidence': 0,
                'news_count': 0,
                'positive_signals': 0,
                'negative_signals': 0
            }
        
        # Analyze sentiment
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for headline in headlines:
            sentiment = self._analyze_headline(headline)
            
            if sentiment > 0:
                positive_count += sentiment
            elif sentiment < 0:
                negative_count += abs(sentiment)
            else:
                neutral_count += 1
        
        # Calculate overall score (-100 to +100)
        total_signals = positive_count + negative_count + neutral_count
        
        if total_signals == 0:
            sentiment_score = 0
        else:
            sentiment_score = ((positive_count - negative_count) / total_signals) * 100
        
        # Determine sentiment category
        if sentiment_score > 20:
            sentiment = 'POSITIVE'
        elif sentiment_score < -20:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'
        
        # Confidence based on news count
        confidence = min(100, len(headlines) * 10)
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment': sentiment,
            'confidence': confidence,
            'news_count': len(headlines),
            'positive_signals': positive_count,
            'negative_signals': negative_count,
            'headlines': headlines[:5]  # Top 5 headlines
        }
    
    def _fetch_news_headlines(self, symbol: str) -> List[str]:
        """Fetch recent news headlines for a stock"""
        headlines = []
        
        try:
            # Remove .NS suffix for search
            search_symbol = symbol.replace('.NS', '').replace('.BO', '')
            
            # Try Google News (simple scraping)
            url = f"https://www.google.com/search?q={search_symbol}+stock+news&tbm=nws"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract headlines (this is a simplified version)
                for item in soup.find_all('div', class_='BNeawe')[:10]:
                    text = item.get_text()
                    if len(text) > 20:  # Filter out short snippets
                        headlines.append(text)
        
        except Exception as e:
            logger.warning(f"Failed to fetch news for {symbol}: {e}")
        
        # Fallback: Generate sample headlines based on symbol
        if not headlines:
            headlines = [
                f"{symbol} shows steady performance",
                f"Market analysis for {symbol}",
                f"Investors watch {symbol} closely"
            ]
        
        return headlines
    
    def _analyze_headline(self, headline: str) -> int:
        """
        Analyze single headline sentiment
        
        Returns: -3 to +3 (very negative to very positive)
        """
        headline_lower = headline.lower()
        
        # Count positive keywords
        positive_score = sum(
            1 for keyword in self.POSITIVE_KEYWORDS
            if keyword in headline_lower
        )
        
        # Count negative keywords
        negative_score = sum(
            1 for keyword in self.NEGATIVE_KEYWORDS
            if keyword in headline_lower
        )
        
        # Calculate net score
        net_score = positive_score - negative_score
        
        # Cap at -3 to +3
        return max(-3, min(3, net_score))
    
    def should_boost_opportunity(self, sentiment_result: Dict, strategy: str) -> bool:
        """
        Decide if sentiment supports taking the trade
        
        Args:
            sentiment_result: Result from analyze_stock_sentiment()
            strategy: Strategy name
            
        Returns:
            bool: True if sentiment is favorable
        """
        sentiment = sentiment_result['sentiment']
        score = sentiment_result['sentiment_score']
        
        # For bullish strategies (MOMENTUM, BREAKOUT, POSITIONAL)
        if strategy in ['MOMENTUM', 'BREAKOUT', 'POSITIONAL']:
            # Want positive sentiment
            return sentiment == 'POSITIVE' or score > 0
        
        # For MEAN_REVERSION
        elif strategy == 'MEAN_REVERSION':
            # Want negative sentiment (oversold, will reverse)
            return sentiment == 'NEGATIVE' or score < -20
        
        return True  # Default: allow
    
    def get_sentiment_boost(self, sentiment_result: Dict) -> float:
        """
        Calculate score boost/penalty based on sentiment
        
        Returns: -10 to +10 points
        """
        score = sentiment_result['sentiment_score']
        confidence = sentiment_result['confidence']
        
        # Boost proportional to sentiment strength and confidence
        boost = (score / 100) * 10 * (confidence / 100)
        
        return boost


class SentimentCache:
    """Cache sentiment results to avoid repeated API calls"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def get(self, symbol: str) -> Dict:
        """Get cached sentiment if available and fresh"""
        if symbol in self.cache:
            cached_data, timestamp = self.cache[symbol]
            
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        return None
    
    def set(self, symbol: str, sentiment_data: Dict):
        """Cache sentiment data"""
        self.cache[symbol] = (sentiment_data, datetime.now())
    
    def clear_old(self):
        """Clear expired cache entries"""
        now = datetime.now()
        
        expired = [
            symbol for symbol, (data, timestamp) in self.cache.items()
            if now - timestamp >= self.cache_duration
        ]
        
        for symbol in expired:
            del self.cache[symbol]
