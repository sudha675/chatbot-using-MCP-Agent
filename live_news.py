import requests
import feedparser
from datetime import datetime, timedelta

NEWSAPI_KEY = "32c62167ae464dc9964185a257a2a0e2"  # Free demo key

def fetch_newsapi_country_news(country: str) -> str:
    """Fetch country-specific news using NewsAPI."""
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=3)
        api_url = "https://newsapi.org/v2/everything"
        params = {
            'q': country,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,
            'apiKey': NEWSAPI_KEY
        }
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            if articles:
                news_items = []
                for article in articles[:8]:
                    title = article.get('title', '').strip()
                    desc = article.get('description', '').strip() or "Latest news update"
                    source = article.get('source', {}).get('name', 'Unknown')
                    url = article.get('url', '#')
                    published = article.get('publishedAt', '')[:10]
                    news_items.append(
                        f"📰 <strong>{title}</strong><br>"
                        f"   📝 {desc[:120]}...<br>"
                        f"   📰 {source} | 🕒 {published} | "
                        f'<a href="{url}" style="color: #667eea; text-decoration: none;" target="_blank">Read More</a>'
                    )
                return f"<strong>📰 {country.upper()} NEWS</strong><br><br>" + "<br><br>".join(news_items)
            else:
                return f"No recent news for {country}."
        else:
            return f"NewsAPI error {response.status_code}."
    except Exception as e:
        return fetch_country_rss_fallback(country)

def fetch_country_rss_fallback(country: str) -> str:
    """Fallback using RSS feeds."""
    country_feeds = {
        'india': ["https://timesofindia.indiatimes.com/rssfeedmostrecent.cms"],
        'usa': ["https://feeds.npr.org/1001/rss.xml"],
        'uk': ["http://feeds.bbci.co.uk/news/rss.xml"]
    }
    if country.lower() not in country_feeds:
        return f"No news sources available for {country}."
    all_items = []
    for rss_url in country_feeds[country.lower()]:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:6]:
                title = getattr(entry, 'title', '').strip()
                link = getattr(entry, 'link', '#')
                published = getattr(entry, 'published', '')[:16]
                all_items.append(
                    f"📰 <strong>{title}</strong><br>"
                    f"   🕒 {published} | "
                    f'<a href="{link}" style="color: #667eea; text-decoration: none;" target="_blank">Read More</a>'
                )
        except:
            continue
    if all_items:
        return f"<strong>📰 {country.upper()} NEWS (RSS)</strong><br><br>" + "<br><br>".join(all_items[:6])
    return f"No {country} news available."

def fetch_breaking_news() -> str:
    """Get global breaking news."""
    try:
        api_url = "https://newsapi.org/v2/top-headlines"
        params = {'country': 'us', 'pageSize': 8, 'apiKey': NEWSAPI_KEY}
        response = requests.get(api_url, params=params, timeout=15)
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            if articles:
                items = []
                for a in articles:
                    title = a.get('title', '').strip()
                    desc = a.get('description', '').strip() or "Breaking news update"
                    source = a.get('source', {}).get('name', 'Unknown')
                    url = a.get('url', '#')
                    items.append(
                        f"🚨 <strong>{title}</strong><br>"
                        f"   📝 {desc[:100]}...<br>"
                        f"   📰 {source} | "
                        f'<a href="{url}" style="color: #667eea;" target="_blank">Read More</a>'
                    )
                return "🚨 <strong>BREAKING NEWS</strong><br><br>" + "<br><br>".join(items)
        return "Breaking news temporarily unavailable."
    except Exception:
        return "Breaking news service error."

def fetch_live_news(query: str) -> str:
    """Main function with country detection."""
    query_lower = query.lower().strip()
    country_map = {
        'india': ['india', 'indian'], 'usa': ['usa', 'us', 'united states'],
        'uk': ['uk', 'united kingdom'], 'canada': ['canada'],
        'australia': ['australia'], 'germany': ['germany'], 'france': ['france']
    }
    detected = None
    for country, keywords in country_map.items():
        if any(k in query_lower for k in keywords):
            detected = country
            break
    if 'breaking' in query_lower:
        return fetch_breaking_news()
    if detected:
        return fetch_newsapi_country_news(detected)
    if 'news' in query_lower:
        return fetch_newsapi_country_news('india')
    return fetch_newsapi_country_news(query)