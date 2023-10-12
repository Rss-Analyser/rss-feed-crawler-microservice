import csv
import os
import requests
import yaml
from bs4 import BeautifulSoup
import re
from PyPDF2 import PdfFileReader
from io import BytesIO

class WebCrawler:
    def __init__(self, base_url, max_depth=3):
        self.base_url = base_url
        self.visited_urls = set()  # To keep track of visited URLs
        self.max_depth = max_depth

    @staticmethod
    def _is_valid_url(url):
        """Validate the URL structure to avoid invalid ones."""
        parsed_url = requests.utils.urlparse(url)
        return all([parsed_url.scheme, parsed_url.netloc, parsed_url.path])

    def _extract_links_from_text(self, content):
        rss_links = set()
        # Improved regex pattern that avoids capturing unwanted HTML tags
        url_pattern = re.compile(
            r'https?://[\w\d\-._~:/?#[\]@!$&\'()*+,;=%]+')
        links = re.findall(url_pattern, content)
        for link in links:
            if (link.endswith(('.rss', '.rss.xml', '.xml')) or 'rss' in link or 'feed' in link) and self._is_valid_url(link):
                rss_links.add(link)
        return rss_links

    def _parse_opml_content(self, content):
        soup = BeautifulSoup(content, 'xml')  # Parse the content as XML
        rss_links = set()

        # Look for <outline> tags with an "xmlUrl" attribute
        for outline in soup.find_all("outline", xmlUrl=True):
            rss_link = outline['xmlUrl']
            if self._is_valid_url(rss_link):  # Validate the URL
                rss_links.add(rss_link)
        
        return rss_links

    def _parse_for_rss_links(self, html, depth=0):
        soup = BeautifulSoup(html, 'html.parser')
        rss_links = set()

        for link in soup.find_all("a", href=True):
            href = link['href']
            if (href.endswith(('.rss', '.rss.xml', '.xml')) or 'rss' in href or 'feed' in href) and self._is_valid_url(href):
                rss_links.add(href)

            # Check for resource type links and recurse if necessary
            elif any(href.endswith(ext) for ext in ['.csv', '.yml', '.yaml', '.opml', '.txt', '.pdf']):
                if depth < self.max_depth and href not in self.visited_urls:  # Check if depth is within limit and URL is not visited
                    self.visited_urls.add(href)
                    rss_links.update(self.crawl(href, depth + 1))  # Recurse

        # Extracting from plain text inside HTML
        rss_links_from_text = self._extract_links_from_text(html)
        rss_links.update(rss_links_from_text)

        return rss_links
    
    def _parse_csv_content(self, content):
        rss_links = set()
        csv_data = csv.reader(content.splitlines())
        for row in csv_data:
            for cell in row:
                links = self._extract_links_from_text(cell.strip())
                rss_links.update(links)
        return rss_links
    
    def _parse_pdf_content(self, content):
        rss_links = set()
        pdf_file = PdfFileReader(BytesIO(content))
        for page_num in range(pdf_file.getNumPages()):
            page = pdf_file.getPage(page_num)
            content = page.extractText()
            links = self._extract_links_from_text(content)
            rss_links.update(links)
        return rss_links
    
    def _parse_yaml_content(self, content):
        try:
            data = yaml.safe_load(content)
            if isinstance(data, list):  # Check if the YAML content is a list of URLs
                return set(filter(self._is_valid_url, data))
            else:
                return set()  # Return an empty set if the YAML format is not as expected
        except yaml.YAMLError:
            print("Error parsing the YAML content")
            return set()

    def crawl(self, url=None, depth=0):
        if not url:
            url = self.base_url

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch content from {url}")
            return set()

        if url.endswith('.csv'):
            # Note: Assuming you have a method named "_parse_csv_content"
            return self._parse_csv_content(response.text)

        if url.endswith(('.yml', '.yaml')):
            # Note: Assuming you have a method named "_parse_yaml_content"
            return self._parse_yaml_content(response.text)

        if url.endswith('.opml'):
            # Note: Assuming you have a method named "_parse_opml_content"
            return self._parse_opml_content(response.text)

        if url.endswith('.txt'):
            return self._extract_links_from_text(response.text)

        if url.endswith('.pdf'):
            # Note: Assuming you have a method named "_parse_pdf_content"
            return self._parse_pdf_content(response.content)

        # If it's none of the above, then parse as HTML
        return self._parse_for_rss_links(response.text, depth)