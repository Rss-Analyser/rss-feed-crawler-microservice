import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

from flask import Flask, request, jsonify
import threading
from rssFeedCrawler import WebCrawler  # Change 'your_crawler_script_name' to the actual name of your script
import sqlite3
import yaml

CONFIG_PATH = "./config.yaml"

# Load config from config.yaml
with open(CONFIG_PATH, 'r') as file:
    config = yaml.safe_load(file)

"dbname=rss_db user=YOUR_USER password=YOUR_PASSWORD host=YOUR_HOST port=YOUR_PORT" = config['database']['sqlite_path']

RSS_FEED_WEBSITES_TABLE_NAME = config['database']['website_table_name']
RSS_LINKS_TABLE_NAME = config['database']['rss_links_table_name']

def add_to_database(url):
    """Add a URL to the SQLite database if it's not already present."""
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT OR IGNORE INTO {RSS_FEED_WEBSITES_TABLE_NAME} (website) VALUES (?)", (url,))
        conn.commit()

app = Flask(__name__)

# Use a global variable to track the crawler status.
CRAWLER_STATUS = "idle"
TOTAL_WEBSITES = 0
TOTAL_LINKS_FOUND = 0
NEW_LINKS_ADDED = 0

def run_crawler():
    global CRAWLER_STATUS, TOTAL_WEBSITES, TOTAL_LINKS_FOUND, NEW_LINKS_ADDED

    # Reset counters at the start of a new crawl
    TOTAL_WEBSITES = 0
    TOTAL_LINKS_FOUND = 0
    NEW_LINKS_ADDED = 0
    
    # Load URLs to be crawled from SQLite DB
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT website FROM {RSS_FEED_WEBSITES_TABLE_NAME}")
        urls_to_crawl = [row[0] for row in cursor.fetchall()]

    # For storing the links found during crawling
    all_found_links = set()

    # Crawl each website
    for website_url in urls_to_crawl:
        TOTAL_WEBSITES += 1  # Increment the websites counter
        crawler = WebCrawler(website_url)
        new_links = crawler.crawl()
        all_found_links.update(new_links)

    TOTAL_LINKS_FOUND = len(all_found_links)  # Update the links found counter

    # Save the crawled links into the SQLite database and count new links
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.cursor()
        for link in all_found_links:
            cursor.execute(f"INSERT OR IGNORE INTO {RSS_LINKS_TABLE_NAME} (link) VALUES (?)", (link,))
            # If a new link was added (lastrowid returns the ID of the last row, which is non-zero if a new row was added)
            if cursor.lastrowid:
                NEW_LINKS_ADDED += 1
        conn.commit()

    # Set the status back to "idle" once crawling is done
    CRAWLER_STATUS = "idle"

@app.route('/start-crawl', methods=['POST'])
def start_crawl():

    global CRAWLER_STATUS
    urls = request.json.get('urls', [])
    
    # Add URLs to the database if not already present
    # Assuming you have a function 'add_to_database' in your main script
    for url in urls:
        add_to_database(url)
    
    if CRAWLER_STATUS == "idle":
        CRAWLER_STATUS = "running"
        # Run the crawler in a separate thread so it doesn't block the main thread

        threading.Thread(target=run_crawler).start()
        
        return jsonify({"message": "Crawling started."})
    else:
        return jsonify({"message": "Crawler is already running."})

@app.route('/status', methods=['GET'])
def get_status():
    global CRAWLER_STATUS, TOTAL_WEBSITES, TOTAL_LINKS_FOUND, NEW_LINKS_ADDED
    return jsonify({
        "status": CRAWLER_STATUS,
        "websites_crawled": TOTAL_WEBSITES,
        "total_links_found": TOTAL_LINKS_FOUND,
        "new_links_added": NEW_LINKS_ADDED
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
