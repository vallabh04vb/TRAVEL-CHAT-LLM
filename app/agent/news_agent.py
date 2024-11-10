import requests
from .config import NEWS_API_KEY, NEWS_API_URL

class NewsAgent:
    @staticmethod
    def get_news(city: str) -> str:
        params = {
            "q": city,
            "apiKey": NEWS_API_KEY,
            "sortBy": "relevance",
            "language": "en"
        }
        
        try:
            response = requests.get(NEWS_API_URL, params=params)
            response.raise_for_status()  # Raises an HTTPError for non-200 responses

            data = response.json()
            articles = data.get("articles", [])

            if articles:
                top_article = articles[0]
                title = top_article.get("title", "No title available")
                description = top_article.get("description", "No description available")
                url = top_article.get("url", "#")
                return f"Top news in {city}: {title}. {description}. Read more: {url}"
            else:
                return f"No recent news found for {city}."
        
        except requests.exceptions.RequestException as e:
            # Handle network-related errors
            return f"Unable to retrieve news data at the moment. Error: {e}"
        except ValueError:
            # Handle JSON parsing errors
            return "Error parsing news data. Please try again later."

