"""
Advanced Real-Time Web Search Module
Enhances the base DataProvider with multi-engine search, content extraction,
and intelligent result processing.
"""

import os
import re
import json
import time
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import feedparser


@dataclass
class EnhancedSearchResult:
    title: str
    snippet: str
    url: str
    source: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    score: float = 0.0
    content: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None


@dataclass
class NewsArticle:
    title: str
    summary: str
    url: str
    published: str
    source: str
    category: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class ExtractedContent:
    url: str
    title: str
    content: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    images: List[str] = None
    links: List[str] = None
    reading_time: Optional[int] = None


class AdvancedWebSearch:
    def __init__(self, cache_dir: str = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_dir = cache_dir or os.path.join(self.base_dir, "data", "search_cache")
        self.cache_file = os.path.join(self.cache_dir, "search_cache.json")
        self.content_cache_file = os.path.join(self.cache_dir, "content_cache.json")
        
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.search_cache = self._load_cache(self.cache_file, ttl_hours=1)
        self.content_cache = self._load_cache(self.content_cache_file, ttl_hours=24)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _load_cache(self, cache_file: str, ttl_hours: int = 1) -> Dict:
        """Load cache from disk if it exists and is not expired."""
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                # Remove expired entries
                current_time = time.time()
                ttl_seconds = ttl_hours * 3600
                cache = {k: v for k, v in cache.items() 
                        if current_time - v.get('timestamp', 0) < ttl_seconds}
                return cache
            except Exception:
                pass
        return {}

    def _save_cache(self, cache: Dict, cache_file: str):
        """Save cache to disk."""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass

    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate a cache key from query and parameters."""
        key_str = f"{query}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def multi_engine_search(self, query: str, max_results: int = 10, 
                           engines: List[str] = None, time_filter: str = None,
                           content_type: str = "web") -> List[EnhancedSearchResult]:
        """
        Search across multiple engines for comprehensive results.
        
        Args:
            query: Search query
            max_results: Maximum results per engine
            engines: List of engines to use ['duckduckgo', 'google', 'bing', 'wikipedia']
            time_filter: Time filter ['day', 'week', 'month', 'year']
            content_type: Type of content ['web', 'news', 'images', 'videos']
        """
        if engines is None:
            engines = ['duckduckgo', 'wikipedia']
        
        cache_key = self._get_cache_key(query, engines=engines, time_filter=time_filter, 
                                        content_type=content_type, max_results=max_results)
        
        if cache_key in self.search_cache:
            cached_results = self.search_cache[cache_key]['data']
            return [EnhancedSearchResult(**r) for r in cached_results]
        
        all_results = []
        
        for engine in engines:
            try:
                if engine == 'duckduckgo':
                    results = self._duckduckgo_search(query, max_results, time_filter, content_type)
                elif engine == 'wikipedia':
                    results = self._wikipedia_search(query, max_results)
                elif engine == 'google':
                    results = self._google_search(query, max_results, time_filter, content_type)
                elif engine == 'bing':
                    results = self._bing_search(query, max_results, time_filter, content_type)
                else:
                    continue
                
                all_results.extend(results)
            except Exception as e:
                print(f"[AdvancedWebSearch] {engine} search failed: {e}")
                continue
        
        # Deduplicate and score results
        unique_results = self._deduplicate_results(all_results)
        scored_results = self._score_results(unique_results, query)
        
        # Sort by score and limit
        scored_results.sort(key=lambda x: x.score, reverse=True)
        final_results = scored_results[:max_results * len(engines)]
        
        # Cache results
        self.search_cache[cache_key] = {
            'data': [asdict(r) for r in final_results],
            'timestamp': time.time()
        }
        self._save_cache(self.search_cache, self.cache_file)
        
        return final_results

    def _duckduckgo_search(self, query: str, max_results: int, 
                          time_filter: str, content_type: str) -> List[EnhancedSearchResult]:
        """Enhanced DuckDuckGo search with multiple content types."""
        results = []
        
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                if content_type == "news":
                    for r in ddgs.news(query, max_results=max_results, timelimit=time_filter or "d"):
                        results.append(EnhancedSearchResult(
                            title=r.get("title", ""),
                            snippet=r.get("body", ""),
                            url=r.get("url", ""),
                            source="duckduckgo_news",
                            published_date=r.get("date"),
                            score=0.8
                        ))
                elif content_type == "images":
                    for r in ddgs.images(query, max_results=max_results):
                        results.append(EnhancedSearchResult(
                            title=r.get("title", ""),
                            snippet=r.get("title", ""),
                            url=r.get("url", ""),
                            source="duckduckgo_images",
                            image_url=r.get("image"),
                            score=0.7
                        ))
                elif content_type == "videos":
                    for r in ddgs.videos(query, max_results=max_results):
                        results.append(EnhancedSearchResult(
                            title=r.get("title", ""),
                            snippet=r.get("content", ""),
                            url=r.get("url", ""),
                            source="duckduckgo_videos",
                            video_url=r.get("content"),
                            score=0.7
                        ))
                else:  # web search
                    for r in ddgs.text(query, max_results=max_results, timelimit=time_filter or "y"):
                        results.append(EnhancedSearchResult(
                            title=r.get("title", ""),
                            snippet=r.get("body", ""),
                            url=r.get("href", ""),
                            source="duckduckgo",
                            score=0.75
                        ))
        except Exception as e:
            # Fallback to HTML scraping
            results = self._duckduckgo_fallback(query, max_results)
        
        return results

    def _duckduckgo_fallback(self, query: str, max_results: int) -> List[EnhancedSearchResult]:
        """Fallback HTML scraping for DuckDuckGo."""
        results = []
        try:
            from urllib.parse import quote
            url = f"https://duckduckgo.com/html/?q={quote(query)}"
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for r in soup.select(".result")[:max_results]:
                a = r.select_one(".result__a")
                s = r.select_one(".result__snippet")
                if a:
                    results.append(EnhancedSearchResult(
                        title=a.get_text(strip=True),
                        snippet=s.get_text(strip=True) if s else "",
                        url=a.get("href", ""),
                        source="duckduckgo_fallback",
                        score=0.6
                    ))
        except Exception as e:
            print(f"[AdvancedWebSearch] DuckDuckGo fallback failed: {e}")
        
        return results

    def _wikipedia_search(self, query: str, max_results: int) -> List[EnhancedSearchResult]:
        """Search Wikipedia for encyclopedic content."""
        results = []
        try:
            import wikipedia
            wikipedia.set_lang("en")
            
            # Search pages
            search_results = wikipedia.search(query, results=max_results)
            
            for title in search_results[:max_results]:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    results.append(EnhancedSearchResult(
                        title=page.title,
                        snippet=page.summary[:500] + "...",
                        url=page.url,
                        source="wikipedia",
                        content=page.content[:2000],
                        score=0.9
                    ))
                except wikipedia.exceptions.DisambiguationError:
                    continue
                except wikipedia.exceptions.PageError:
                    continue
        except Exception as e:
            print(f"[AdvancedWebSearch] Wikipedia search failed: {e}")
        
        return results

    def _google_search(self, query: str, max_results: int, 
                      time_filter: str, content_type: str) -> List[EnhancedSearchResult]:
        """Google search using custom search API or scraping."""
        results = []
        
        # Try using Google Custom Search API if key is available
        google_api_key = os.environ.get('GOOGLE_API_KEY')
        google_cx = os.environ.get('GOOGLE_CX')
        
        if google_api_key and google_cx:
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    ' key': google_api_key,
                    'cx': google_cx,
                    'q': query,
                    'num': max_results
                }
                
                if time_filter:
                    params['dateRestrict'] = f"d{self._time_filter_to_days(time_filter)}"
                
                resp = self.session.get(url, params=params, timeout=10)
                data = resp.json()
                
                for item in data.get('items', []):
                    results.append(EnhancedSearchResult(
                        title=item.get('title', ''),
                        snippet=item.get('snippet', ''),
                        url=item.get('link', ''),
                        source="google_api",
                        published_date=item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time'),
                        score=0.85
                    ))
            except Exception as e:
                print(f"[AdvancedWebSearch] Google API search failed: {e}")
        
        return results

    def _bing_search(self, query: str, max_results: int, 
                    time_filter: str, content_type: str) -> List[EnhancedSearchResult]:
        """Bing search using Azure API or scraping."""
        results = []
        
        bing_api_key = os.environ.get('BING_API_KEY')
        if bing_api_key:
            try:
                url = "https://api.bing.microsoft.com/v7.0/search"
                headers = {'Ocp-Apim-Subscription-Key': bing_api_key}
                params = {
                    'q': query,
                    'count': max_results,
                    'responseFilter': 'webpages'
                }
                
                if time_filter:
                    params['freshness'] = time_filter
                
                resp = self.session.get(url, headers=headers, params=params, timeout=10)
                data = resp.json()
                
                for item in data.get('webPages', {}).get('value', []):
                    results.append(EnhancedSearchResult(
                        title=item.get('name', ''),
                        snippet=item.get('snippet', ''),
                        url=item.get('url', ''),
                        source="bing_api",
                        published_date=item.get('datePublished'),
                        score=0.82
                    ))
            except Exception as e:
                print(f"[AdvancedWebSearch] Bing API search failed: {e}")
        
        return results

    def _time_filter_to_days(self, time_filter: str) -> int:
        """Convert time filter string to days."""
        mapping = {'day': 1, 'week': 7, 'month': 30, 'year': 365}
        return mapping.get(time_filter.lower(), 365)

    def _deduplicate_results(self, results: List[EnhancedSearchResult]) -> List[EnhancedSearchResult]:
        """Remove duplicate results based on URL similarity."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # Normalize URL for comparison
            url = urlparse(result.url).netloc + urlparse(result.url).path
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results

    def _score_results(self, results: List[EnhancedSearchResult], query: str) -> List[EnhancedSearchResult]:
        """Score results based on relevance to query."""
        query_terms = set(query.lower().split())
        
        for result in results:
            score = result.score
            
            # Boost for title matches
            title_lower = result.title.lower()
            title_matches = sum(1 for term in query_terms if term in title_lower)
            score += (title_matches / len(query_terms)) * 0.2
            
            # Boost for snippet matches
            snippet_lower = result.snippet.lower()
            snippet_matches = sum(1 for term in query_terms if term in snippet_lower)
            score += (snippet_matches / len(query_terms)) * 0.1
            
            # Boost for authoritative sources
            authoritative_domains = ['wikipedia.org', 'scholar.google.com', 'nature.com', 
                                    'science.org', 'gov', 'edu', 'reuters.com', 'apnews.com']
            if any(domain in result.url for domain in authoritative_domains):
                score += 0.15
            
            # Boost for recent content
            if result.published_date:
                try:
                    pub_date = datetime.fromisoformat(result.published_date.replace('Z', '+00:00'))
                    days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
                    if days_old < 7:
                        score += 0.1
                    elif days_old < 30:
                        score += 0.05
                except Exception:
                    pass
            
            result.score = min(score, 1.0)
        
        return results

    def get_real_time_news(self, query: str = None, category: str = None, 
                          max_results: int = 20) -> List[NewsArticle]:
        """
        Get real-time news from RSS feeds and news APIs.
        
        Args:
            query: Search query for news
            category: News category ['technology', 'business', 'science', 'health', 'sports']
            max_results: Maximum number of articles
        """
        articles = []
        
        # RSS feeds for different categories
        rss_feeds = {
            'technology': [
                'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'https://www.theverge.com/rss/index.xml',
                'https://techcrunch.com/feed/'
            ],
            'business': [
                'http://feeds.bbci.co.uk/news/business/rss.xml',
                'https://www.bloomberg.com/feed/news/',
                'https://feeds.reuters.com/reuters/businessNews'
            ],
            'science': [
                'http://feeds.bbci.co.uk/news/science/rss.xml',
                'https://www.science.org/rss/news_current.xml',
                'https://feeds.reuters.com/reuters/scienceNews'
            ],
            'health': [
                'http://feeds.bbci.co.uk/news/health/rss.xml',
                'https://www.who.int/rss/feed'
            ],
            'general': [
                'http://feeds.bbci.co.uk/news/rss.xml',
                'https://feeds.reuters.com/reuters/topNews',
                'https://feeds.apnews.com/apf-topnews'
            ]
        }
        
        feeds_to_check = rss_feeds.get(category, rss_feeds['general'])
        
        for feed_url in feeds_to_check:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:max_results // len(feeds_to_check)]:
                    # Filter by query if provided
                    if query:
                        title_lower = entry.get('title', '').lower()
                        summary_lower = entry.get('summary', '').lower()
                        if query.lower() not in title_lower and query.lower() not in summary_lower:
                            continue
                    
                    article = NewsArticle(
                        title=entry.get('title', ''),
                        summary=self._clean_html(entry.get('summary', '')),
                        url=entry.get('link', ''),
                        published=entry.get('published', ''),
                        source=feed.feed.get('title', feed_url),
                        image_url=self._extract_image_url(entry),
                        category=category
                    )
                    articles.append(article)
                    
            except Exception as e:
                print(f"[AdvancedWebSearch] Failed to parse RSS feed {feed_url}: {e}")
                continue
        
        # Sort by publication date
        articles.sort(key=lambda x: x.published, reverse=True)
        
        return articles[:max_results]

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(strip=True)

    def _extract_image_url(self, entry) -> Optional[str]:
        """Extract image URL from RSS entry."""
        if hasattr(entry, 'enclosures') and entry.enclosures:
            return entry.enclosures[0].get('href')
        
        # Try to extract from summary
        summary = entry.get('summary', '')
        soup = BeautifulSoup(summary, 'html.parser')
        img = soup.find('img')
        if img:
            return img.get('src')
        
        return None

    def extract_content(self, url: str, max_length: int = 10000) -> ExtractedContent:
        """
        Extract and clean content from a URL.
        
        Args:
            url: URL to extract content from
            max_length: Maximum content length in characters
        """
        cache_key = self._get_cache_key(url)
        
        if cache_key in self.content_cache:
            cached = self.content_cache[cache_key]['data']
            return ExtractedContent(**cached)
        
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else url
            
            # Extract main content
            content = ""
            content_tags = ['article', 'main', 'div.content', 'div.post', 'div.entry-content']
            
            for tag in content_tags:
                element = soup.find(tag)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    if len(content) > 500:
                        break
            
            if not content or len(content) < 500:
                content = soup.get_text(separator='\n', strip=True)
            
            # Clean up content
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content[:max_length]
            
            # Extract images
            images = []
            for img in soup.find_all('img')[:20]:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    images.append(urljoin(url, img_url))
            
            # Extract links
            links = []
            for a in soup.find_all('a', href=True)[:50]:
                links.append(urljoin(url, a['href']))
            
            # Estimate reading time
            word_count = len(content.split())
            reading_time = max(1, word_count // 200)
            
            # Try to extract author
            author = None
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                author = author_meta.get('content')
            
            # Try to extract publish date
            published_date = None
            date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if date_meta:
                published_date = date_meta.get('content')
            
            extracted = ExtractedContent(
                url=url,
                title=title_text,
                content=content,
                author=author,
                published_date=published_date,
                images=images,
                links=links,
                reading_time=reading_time
            )
            
            # Cache result
            self.content_cache[cache_key] = {
                'data': asdict(extracted),
                'timestamp': time.time()
            }
            self._save_cache(self.content_cache, self.content_cache_file)
            
            return extracted
            
        except Exception as e:
            raise RuntimeError(f"Content extraction failed for {url}: {e}")

    def search_and_extract(self, query: str, max_results: int = 5, 
                          extract_content: bool = True) -> List[Dict]:
        """
        Search and optionally extract full content from results.
        
        Args:
            query: Search query
            max_results: Maximum search results
            extract_content: Whether to extract full content from URLs
        """
        search_results = self.multi_engine_search(query, max_results=max_results)
        
        if not extract_content:
            return [asdict(r) for r in search_results]
        
        enhanced_results = []
        for result in search_results:
            result_dict = asdict(result)
            
            try:
                content = self.extract_content(result.url)
                result_dict['full_content'] = content.content
                result_dict['author'] = content.author
                result_dict['published_date'] = content.published_date
                result_dict['reading_time'] = content.reading_time
            except Exception as e:
                print(f"[AdvancedWebSearch] Failed to extract content from {result.url}: {e}")
                result_dict['full_content'] = None
            
            enhanced_results.append(result_dict)
        
        return enhanced_results

    def get_trending_topics(self, category: str = None) -> List[Dict]:
        """
        Get trending topics from various sources.
        
        Args:
            category: Category filter ['technology', 'business', 'science', 'general']
        """
        trending = []
        
        # Google Trends (via RSS)
        try:
            trends_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
            feed = feedparser.parse(trends_url)
            
            for entry in feed.entries[:10]:
                trending.append({
                    'title': entry.get('title', ''),
                    'traffic': entry.get('ht_approx_traffic', ''),
                    'source': 'google_trends',
                    'url': entry.get('link', '')
                })
        except Exception as e:
            print(f"[AdvancedWebSearch] Google Trends failed: {e}")
        
        # Twitter trends (would need API key)
        # Reddit trending (would need API access)
        
        return trending

    def clear_cache(self):
        """Clear all search and content caches."""
        self.search_cache.clear()
        self.content_cache.clear()
        self._save_cache(self.search_cache, self.cache_file)
        self._save_cache(self.content_cache, self.content_cache_file)
