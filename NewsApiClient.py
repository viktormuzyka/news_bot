import requests

class NewsApiClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_news_by_topic(self, topic, language_code, date_from=""):
        news_api_url = f'https://newsapi.org/v2/everything?q={topic}&apiKey={self.api_key}&pageSize=100'
        if language_code and language_code != "dont!":
            news_api_url += f"&language={language_code}"

        if date_from:
            news_api_url += f"&from={date_from}"

        print(news_api_url)
        response = requests.get(news_api_url)
        data = response.json()
        news_results = [{'title': article['title'], 'url': article['url']} for article in data['articles']]
        print(news_results)
        return news_results
