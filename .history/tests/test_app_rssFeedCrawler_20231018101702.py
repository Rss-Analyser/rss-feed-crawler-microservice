import requests
import json
import time

BASE_URL = "http://localhost:5001"  # Assuming your microservice is running locally on port 5000

def test_start_crawl_with_urls():
    print("Testing /start-crawl with URLs...")
    payload = {
        "urls": [
            "https://github.com/plenaryapp/awesome-rss-feeds",
            "https://raw.githubusercontent.com/androidsx/micro-rss/master/list-of-feeds.txt",
            "https://github.com/joshuawalcher/rssfeeds",
            "https://raw.githubusercontent.com/impressivewebs/frontend-feeds/master/frontend-feeds.opml",
            "https://raw.githubusercontent.com/tuan3w/awesome-tech-rss/main/feeds.opml",
            "https://github.com/plenaryapp/awesome-rss-feeds/tree/master/recommended/with_category",
            "https://github.com/plenaryapp/awesome-rss-feeds/tree/master/countries/without_category",
            "https://gist.githubusercontent.com/stungeye/fe88fc810651174d0d180a95d79a8d97/raw/35cf2dc0db2c28aac21d03709592567c3fc60180/crypto_news.json",
            "https://raw.githubusercontent.com/yavuz/news-feed-list-of-countries/master/news-feed-list-of-countries.json",
            "https://raw.githubusercontent.com/git-list/security-rss-list/master/README.md"
        ]
    }
    response = requests.post(f"{BASE_URL}/start-crawl", json=payload)
    data = response.json()
    print(f"Response: {data}\n")

def test_start_crawl_without_urls():
    print("Testing /start-crawl without URLs...")
    response = requests.post(f"{BASE_URL}/start-crawl")
    data = response.json()
    print(f"Response: {data}\n")

def test_status():
    print("Testing /status...")
    response = requests.get(f"{BASE_URL}/status")
    data = response.json()
    
    # Print all the data received from the endpoint
    for key, value in data.items():
        print(f"{key.capitalize()}: {value}")
    
    print("\n")
    
    return data.get('status', 'unknown')  # fetch the status or default to 'unknown'

if __name__ == "__main__":
    test_start_crawl_with_urls()
    # test_start_crawl_without_urls()
    
    while test_status() != "idle":
        time.sleep(1)
