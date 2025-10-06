import requests
import feedparser
import urllib.parse
from datetime import datetime, timedelta

# NewsAPI Configuration
NEWSAPI_KEY = "0de38909cc3f4083b9071d135412fd12"

def fetch_newsapi_articles(query: str, page_size: int = 8) -> str:
    """
    Fetch live news using NewsAPI - Most reliable source
    """
    try:
        # Calculate dates for recent news (last 7 days for better results)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=7)
        
        api_url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',  # Changed to publishedAt for latest news
            'pageSize': page_size,
            'apiKey': NEWSAPI_KEY
        }
        
        print(f"🔍 NewsAPI searching for: {query}")
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            total_results = data.get('totalResults', 0)
            
            if articles:
                news_items = []
                for i, article in enumerate(articles, 1):
                    title = article.get('title', '').strip()
                    description = article.get('description', '').strip()
                    source = article.get('source', {}).get('name', 'Unknown')
                    url = article.get('url', '#')
                    published = article.get('publishedAt', '')[:10]  # Get just the date
                    
                    # Skip articles with no title
                    if not title or title == '[Removed]':
                        continue
                        
                    # Use description or create a placeholder
                    if not description or description == '[Removed]':
                        description = "No description available"
                    
                    news_items.append(
                        f"**{i}. {title}**\n"
                        f"   📝 {description}\n"
                        f"   📰 {source} | 🕒 {published}\n"
                        f"   🔗 [Read more]({url})"
                    )
                
                if news_items:
                    result = f"📰 **Latest News for '{query}'**\n\n"
                    result += "\n\n".join(news_items)
                    return result
                else:
                    return f"❌ No valid articles found for '{query}'"
            else:
                return f"❌ No articles found for '{query}'"
        else:
            error_msg = f"NewsAPI Error {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('message', 'Unknown error')
                error_msg += f": {error_detail}"
            except:
                pass
            return f"❌ {error_msg}"
            
    except Exception as e:
        print(f"❌ NewsAPI Error: {e}")
        return f"❌ News service temporarily unavailable: {str(e)}"

def fetch_top_headlines() -> str:
    """
    Fetch top headlines for general news
    """
    try:
        api_url = "https://newsapi.org/v2/top-headlines"
        params = {
            'country': 'us',
            'pageSize': 10,
            'apiKey': NEWSAPI_KEY
        }
        
        print("📰 Fetching top headlines...")
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                news_items = []
                for i, article in enumerate(articles, 1):
                    title = article.get('title', '').strip()
                    description = article.get('description', '').strip()
                    source = article.get('source', {}).get('name', 'Unknown')
                    url = article.get('url', '#')
                    
                    if not title or title == '[Removed]':
                        continue
                        
                    if not description or description == '[Removed]':
                        description = "No description available"
                    
                    news_items.append(
                        f"**{i}. {title}**\n"
                        f"   📝 {description}\n"
                        f"   📰 {source}\n"
                        f"   🔗 [Read more]({url})"
                    )
                
                if news_items:
                    return "📰 **Top Headlines Today**\n\n" + "\n\n".join(news_items)
            
            return "❌ No headlines available at the moment"
        else:
            return f"❌ Headlines service error: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Headlines Error: {e}")
        return f"❌ Headlines service unavailable: {str(e)}"

def fetch_google_news_rss(query: str) -> str:
    """
    Fetch news from Google News RSS feed (Fallback)
    """
    try:
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        print(f"📡 Google RSS searching for: {query}")
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            return ""

        news_items = []
        for i, entry in enumerate(feed.entries[:5], 1):
            title = getattr(entry, 'title', 'No title').strip()
            summary = getattr(entry, 'summary', 'No description').strip()
            link = getattr(entry, 'link', '#')
            published = getattr(entry, 'published', 'Unknown date')
            
            if title and title != 'No title':
                # Clean up summary
                if len(summary) > 150:
                    summary = summary[:150] + '...'
                
                news_items.append(
                    f"**{i}. {title}**\n"
                    f"   📝 {summary}\n"
                    f"   🕒 {published}\n"
                    f"   🔗 [Read more]({link})"
                )
        
        if news_items:
            return f"📡 **Additional News Sources**\n\n" + "\n\n".join(news_items)
        return ""
        
    except Exception as e:
        print(f"❌ Google RSS Error: {e}")
        return ""

def fetch_live_news(query: str) -> str:
    """
    Main function to fetch live news from all sources
    """
    try:
        # If query is about general/today's news, use top headlines
        if query.lower() in ['today', 'latest', 'current', 'news', 'headlines', 'breaking', 'latest news', 'today news']:
            return fetch_top_headlines()
        
        all_results = []
        
        # 1. NewsAPI (Primary - most reliable)
        newsapi_results = fetch_newsapi_articles(query)
        if newsapi_results and "❌" not in newsapi_results:
            all_results.append(newsapi_results)
        
        # 2. Google News RSS (Secondary)
        google_results = fetch_google_news_rss(query)
        if google_results:
            all_results.append(google_results)
        
        if all_results:
            final_result = "\n\n".join(all_results)
            return final_result
        else:
            return f"❌ **No news found for '{query}'**\n\nTry:\n• Using different keywords\n• Checking your spelling\n• Using more general terms"
            
    except Exception as e:
        return f"❌ **Search error**: {str(e)}"

def fetch_recent_event_info(query: str) -> str:
    """
    Alias for fetch_live_news for backward compatibility
    """
    return fetch_live_news(query)

def fetch_breaking_news() -> str:
    """Get breaking news headlines"""
    return fetch_top_headlines()

def fetch_technology_news() -> str:
    """Get technology news"""
    return fetch_live_news("technology")

def fetch_sports_news() -> str:
    """Get sports news"""
    return fetch_live_news("sports")

def fetch_business_news() -> str:
    """Get business news"""
    return fetch_live_news("business")

# Test function
def test_news_search():
    """Test the news search functionality"""
    test_queries = [
        "today",
        "technology",
        "sports",
        "politics"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print(f"{'='*60}")
        result = fetch_live_news(query)
        print(result)
        print(f"{'='*60}")

if __name__ == "__main__":
    test_news_search()