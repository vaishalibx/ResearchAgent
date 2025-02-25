# research_agent/news.py
import requests

# Function to fetch trending articles based on keywords
def fetch_trending_articles(api_key, keywords):
    url = "https://newsapi.org/v2/everything"
    articles = []

    for keyword in keywords:
        params = {
            'q': keyword,  # Search for the keyword
            'sortBy': 'popularity',  # Sort by popularity
            'apiKey': api_key,  # Your API key
            'language': 'en',  # Language of articles
            'pageSize': 5 # Number of articles to fetch
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            articles.extend(data.get('articles', []))
        else:
            print(f"Error fetching articles for keyword '{keyword}': {response.status_code}")

    return articles