# live_news.py
import requests
import feedparser
import urllib.parse
from datetime import datetime, timedelta
import re

# NewsAPI Configuration - Use this free key
NEWSAPI_KEY = "32c62167ae464dc9964185a257a2a0e2"  # Free demo key

def fetch_newsapi_country_news(country: str) -> str:
    """
    Fetch country-specific news using NewsAPI with proper query filtering
    """
    try:
        # Country-specific search terms
        country_queries = {
            'india': [
                "India", "Indian", "Delhi", "Mumbai", "Chennai", "Kolkata", 
                "Bangalore", "Modi", "BJP", "Congress", "Indian government",
                "Indian economy", "Indian politics", "Bollywood", "Indian cricket"
            ],
            'usa': [
                "United States", "USA", "US", "Washington", "Biden", "Trump",
                "White House", "Congress", "Senate", "American", "US politics",
                "US economy", "New York", "California", "Texas", "Florida"
            ],
            'uk': [
                "United Kingdom", "UK", "Britain", "London", "British",
                "Prime Minister", "Parliament", "Brexit", "England", "Scotland",
                "Wales", "Northern Ireland", "UK politics", "UK economy"
            ],
            'canada': [
                "Canada", "Canadian", "Ottawa", "Toronto", "Vancouver",
                "Trudeau", "Canadian government", "Canadian politics"
            ],
            'australia': [
                "Australia", "Australian", "Sydney", "Melbourne", "Canberra",
                "Australian government", "Australian politics"
            ],
            'germany': [
                "Germany", "German", "Berlin", "Merkel", "German politics",
                "German economy", "European Union"
            ],
            'france': [
                "France", "French", "Paris", "Macron", "French politics",
                "French economy"
            ],
            'japan': [
                "Japan", "Japanese", "Tokyo", "Japanese government",
                "Japanese economy", "Japanese politics"
            ]
        }
        
        country_lower = country.lower()
        if country_lower in country_queries:
            search_terms = country_queries[country_lower]
            # Use OR operator to search for multiple terms
            query = " OR ".join(search_terms[:5])  # Use first 5 terms
        else:
            query = country
        
        # Calculate date range (last 3 days for fresh news)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=3)
        
        api_url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 15,  # Get more articles to filter
            'apiKey': NEWSAPI_KEY
        }
        
        print(f"🔍 Searching {country.upper()} news with query: {query}")
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            total_results = data.get('totalResults', 0)
            
            print(f"📊 Found {total_results} total results for {country}")
            
            if articles:
                news_items = []
                for i, article in enumerate(articles[:10], 1):
                    title = article.get('title', '').strip()
                    description = article.get('description', '').strip()
                    source = article.get('source', {}).get('name', 'Unknown')
                    url = article.get('url', '#')
                    published = article.get('publishedAt', '')[:10]  # Get date
                    
                    # Skip articles with no title or removed content
                    if not title or title == '[Removed]':
                        continue
                    
                    # Filter to ensure it's actually about the country
                    if not is_about_country(title, description, country_lower):
                        continue
                        
                    # Use description or create a placeholder
                    if not description or description == '[Removed]':
                        description = "Latest news update"
                    else:
                        # Shorten description if too long
                        if len(description) > 120:
                            description = description[:120] + '...'
                    
                    # Get country flag emoji
                    flag_emoji = get_country_flag(country_lower)
                    
                    news_items.append(
                        f"{flag_emoji} <strong>{title}</strong><br>"
                        f"   📝 {description}<br>"
                        f"   📰 {source} | 🕒 {published} | "
                        f'<a href="{url}" style="color: #667eea; text-decoration: none; font-weight: 500;" target="_blank">🔗 Read Full Story</a>'
                    )
                
                if news_items:
                    result = f"<strong>{flag_emoji} {country.upper()} NEWS - LATEST UPDATES</strong><br><br>"
                    result += "<br><br>".join(news_items[:8])  # Show top 8
                    result += f"<br><br>📊 <strong>{len(news_items)} relevant articles filtered from {total_results} total results</strong>"
                    return result
                else:
                    return f"❌ No relevant {country} news found after filtering. Try 'breaking news' for general headlines."
            else:
                return f"❌ No articles found for {country}. The API might be rate limited."
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
        print(f"❌ NewsAPI Error for {country}: {e}")
        return fetch_country_rss_fallback(country)

def is_about_country(title: str, description: str, country: str) -> bool:
    """
    Filter function to ensure news is actually about the specified country
    """
    text = (title + " " + (description or "")).lower()
    
    # Country-specific keywords
    country_keywords = {
        'india': ['india', 'indian', 'delhi', 'mumbai', 'chennai', 'kolkata', 
                 'bangalore', 'modi', 'bjp', 'congress', 'indian', 'bollywood',
                 'indian cricket', 'indian economy', 'indian government'],
        'usa': ['united states', 'usa', 'us', 'washington', 'biden', 'trump',
               'white house', 'congress', 'senate', 'american', 'us politics',
               'new york', 'california', 'texas', 'florida'],
        'uk': ['united kingdom', 'uk', 'britain', 'london', 'british',
              'prime minister', 'parliament', 'brexit', 'england', 'scotland'],
        'canada': ['canada', 'canadian', 'ottawa', 'toronto', 'vancouver', 'trudeau'],
        'australia': ['australia', 'australian', 'sydney', 'melbourne', 'canberra'],
        'germany': ['germany', 'german', 'berlin', 'merkel'],
        'france': ['france', 'french', 'paris', 'macron'],
        'japan': ['japan', 'japanese', 'tokyo']
    }
    
    if country in country_keywords:
        keywords = country_keywords[country]
        return any(keyword in text for keyword in keywords)
    
    return country.lower() in text

def get_country_flag(country: str) -> str:
    """Get flag emoji for country"""
    flag_emojis = {
        'india': '🇮🇳',
        'usa': '🇺🇸', 'us': '🇺🇸',
        'uk': '🇬🇧', 'united kingdom': '🇬🇧',
        'canada': '🇨🇦',
        'australia': '🇦🇺',
        'germany': '🇩🇪',
        'france': '🇫🇷',
        'japan': '🇯🇵',
        'china': '🇨🇳',
        'russia': '🇷🇺',
        'brazil': '🇧🇷'
    }
    return flag_emojis.get(country.lower(), '📰')

def fetch_country_rss_fallback(country: str) -> str:
    """
    Fallback using RSS feeds when NewsAPI fails
    """
    try:
        # Country-specific RSS feeds as fallback
        country_feeds = {
            'india': [
                "https://timesofindia.indiatimes.com/rssfeedmostrecent.cms",
                "https://feeds.feedburner.com/ndtvnews-top-stories"
            ],
            'usa': [
                "https://feeds.npr.org/1001/rss.xml",
                "https://rss.cnn.com/rss/edition.rss"
            ],
            'uk': [
                "http://feeds.bbci.co.uk/news/rss.xml",
                "https://feeds.skynews.com/feeds/rss/home.xml"
            ]
        }
        
        country_lower = country.lower()
        if country_lower not in country_feeds:
            return f"❌ No news sources available for {country}"
        
        all_news_items = []
        flag_emoji = get_country_flag(country)
        
        for rss_url in country_feeds[country_lower]:
            try:
                print(f"📡 Fallback RSS for {country}: {rss_url[:50]}...")
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    for entry in feed.entries[:8]:
                        title = getattr(entry, 'title', '').strip()
                        title = re.sub(r'\s*-\s*[^-]+$', '', title)
                        
                        published = getattr(entry, 'published', '')
                        if published:
                            try:
                                pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                                published = pub_date.strftime('%b %d, %H:%M')
                            except:
                                published = published[:16]
                        
                        link = getattr(entry, 'link', '#')
                        
                        if title and len(title) > 15:
                            # Basic country filtering for RSS
                            if is_about_country(title, "", country_lower):
                                news_item = (
                                    f"{flag_emoji} <strong>{title}</strong><br>"
                                    f"   🕒 {published} | "
                                    f'<a href="{link}" style="color: #667eea; text-decoration: none; font-weight: 500;" target="_blank">🔗 Read Full Story</a>'
                                )
                                if news_item not in all_news_items:
                                    all_news_items.append(news_item)
            except Exception as e:
                print(f"❌ RSS Error for {country}: {e}")
                continue
        
        if all_news_items:
            result = f"<strong>{flag_emoji} {country.upper()} NEWS (RSS Fallback)</strong><br><br>"
            result += "<br><br>".join(all_news_items[:6])
            return result
        else:
            return f"❌ No {country} news available via RSS fallback."
        
    except Exception as e:
        return f"❌ Fallback also failed for {country}: {str(e)}"

def fetch_breaking_news() -> str:
    """Get global breaking news"""
    try:
        api_url = "https://newsapi.org/v2/top-headlines"
        params = {
            'country': 'us',  # Use US as base for global headlines
            'pageSize': 10,
            'apiKey': NEWSAPI_KEY
        }
        
        print("🚨 Fetching breaking news...")
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                news_items = []
                for i, article in enumerate(articles[:8], 1):
                    title = article.get('title', '').strip()
                    description = article.get('description', '').strip()
                    source = article.get('source', {}).get('name', 'Unknown')
                    url = article.get('url', '#')
                    
                    if not title or title == '[Removed]':
                        continue
                        
                    if not description or description == '[Removed]':
                        description = "Breaking news update"
                    else:
                        if len(description) > 100:
                            description = description[:100] + '...'
                    
                    news_items.append(
                        f"🚨 <strong>{title}</strong><br>"
                        f"   📝 {description}<br>"
                        f"   📰 {source} | "
                        f'<a href="{url}" style="color: #667eea; text-decoration: none; font-weight: 500;" target="_blank">🔗 Read More</a>'
                    )
                
                if news_items:
                    result = "🚨 <strong>BREAKING NEWS - GLOBAL</strong><br><br>"
                    result += "<br><br>".join(news_items)
                    return result
            
            return "❌ No breaking news available at the moment."
        else:
            return "❌ Breaking news service temporarily unavailable."
            
    except Exception as e:
        return "❌ Breaking news service error."

def fetch_live_news(query: str) -> str:
    """
    Main function with enhanced country detection
    """
    try:
        query_lower = query.lower().strip()
        
        # Country detection map
        country_map = {
            'india': ['india', 'indian'],
            'usa': ['usa', 'us', 'united states', 'america'],
            'uk': ['uk', 'united kingdom', 'britain'],
            'canada': ['canada', 'canadian'],
            'australia': ['australia'],
            'germany': ['germany'],
            'france': ['france'],
            'japan': ['japan']
        }
        
        # Detect country from query
        detected_country = None
        for country, keywords in country_map.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_country = country
                break
        
        # Handle special cases
        if any(word in query_lower for word in ['breaking', 'headlines']):
            return fetch_breaking_news()
        
        if detected_country:
            return fetch_newsapi_country_news(detected_country)
        
        # Default to India news if query contains "news" but no specific country
        if 'news' in query_lower:
            return fetch_newsapi_country_news('india')
        
        # Generic search
        return fetch_newsapi_country_news(query)
        
    except Exception as e:
        return f"❌ News service error: {str(e)}"

def fetch_recent_event_info(query: str) -> str:
    """Alias for fetch_live_news"""
    return fetch_live_news(query)

# Test function
def test_news():
    """Test the news functionality"""
    print("🧪 TESTING COUNTRY-SPECIFIC NEWS\n")
    
    test_queries = [
        "india",
        "usa", 
        "uk",
        "breaking news"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"Testing: '{query}'")
        print(f"{'='*70}")
        result = fetch_live_news(query)
        # Print without HTML tags for console view
        clean_result = re.sub(r'<[^>]+>', '', result)
        print(clean_result)
        print(f"{'='*70}")

if __name__ == "__main__":
    test_news()