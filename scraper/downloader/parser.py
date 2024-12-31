import requests
import html2text
from bs4 import BeautifulSoup

def extractor(url):
    """
    Fetches the title and content of a webpage and converts the content to Markdown.

    Parameters:
        url (str): The URL of the webpage.

    Returns:
        tuple: A tuple containing the title (str) and Markdown content (str).
    """
    try:
        # Fetch the HTML content
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        # Extract the title using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Untitled"

        # Convert HTML to Markdown
        converter = html2text.HTML2Text()
        converter.ignore_links = False  # Keep links
        converter.ignore_images = False  # Keep images
        converter.bypass_tables = False  # Convert tables

        markdown_content = converter.handle(html_content)
        return title, markdown_content

    except requests.RequestException as e:
        return "Error", f"Error fetching the URL: {e}"
    except Exception as e:
        return "Error", f"Error processing the content: {e}"


