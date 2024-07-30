import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin
import traceback
import re
import os
import logging
import json
from tqdm import tqdm
from file_utils import get_config


def safe_filename(url):
    name = url.split('/')[-1]
    name = unquote(name)
    safe_name = re.sub(r'[^\w\s-]', '_', name)
    return re.sub(r'[-\s]+', '_', safe_name.strip())


# Set up logging
logging.basicConfig(filename='wiki_bot_log.txt',
                    level=logging.INFO, format='%(asctime)s - %(message)s')

wikipedia_base_url = 'https://en.wikipedia.org'


def get_listing_pages(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        soup = BeautifulSoup(response.content, 'lxml')
        listings = soup.select(".navigation-not-searchable a")
        lists = []
        lists_url = []

        for listing in listings:
            lists.append(listing.text)
            lists_url.append(
                urljoin(wikipedia_base_url, listing.attrs['href']))
    except Exception as e:
        print("Failed to fetch the URL")
        print("Error:", str(e))
        traceback.print_exc()  # This prints the stack trace of the exception
    finally:
        return dict(zip(lists_url, lists))


def get_buildings_from_main_page(url):
    response = requests.get(url)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    soup = BeautifulSoup(response.content, 'lxml')
    urls = set(soup.select("#bodyContent table.wikitable tr td:first-child a"))

    html = soup.prettify()
    see_also_html = '<span id="See_also">'
    index = html.find(see_also_html)
    new_html = html[:index]
    soup = BeautifulSoup(new_html, 'lxml')

    selected_urls = set()
    for url in urls:
        url_href = url['href']
        if url_href.startswith('/wiki/') and not url_href.startswith(
                ('/wiki/File:', '/wiki/Category:')) and 'listings' not in url_href:
            selected_urls.add(url_href)

    return selected_urls


def get_buildings_from_listing_pages(listing):
    selected_hrefs = set()
    for url, text in listing.items():
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        soup = BeautifulSoup(response.content, 'lxml')
        lis = soup.select('#mw-content-text li')
        navbar_links = set(link['href']
                           for link in soup.select(".navbox a[href]"))

        see_also_links = set(
            link['href'] for link in soup.find_all('a', href=True) if link.find_previous(id='See_also'))
        references_links = set(
            link['href'] for link in soup.find_all('a', href=True) if link.find_previous(id='References'))
        external_links = set(
            link['href'] for link in soup.find_all('a', href=True) if link.find_previous(id='External_links'))
        cat_links = set(link['href'] for link in soup.find_all(
            'a', href=True) if link.find_previous(id='catlinks'))
        unwanted_links = (see_also_links.union(references_links)
                          .union(external_links).union(cat_links).union(navbar_links))

        for li in lis:
            text_parts = li.contents  # Get all parts of the li tag's contents
            first_part_is_text = (len(text_parts) > 1 and isinstance(
                text_parts[0], str) and text_parts[0].strip())
            if not first_part_is_text:  # Only process li's without text before the link
                a = li.find('a')  # Get only the first <a> tag
                if a and 'href' in a.attrs:  # Ensure 'a' is not None and has 'href' attribute
                    href = a['href']
                    if href.startswith('/wiki/') and not href.startswith(
                            ('/wiki/File:', '/wiki/Category:')) and 'listings' not in href:
                        if not any(unwanted_link == href for unwanted_link in unwanted_links):
                            selected_hrefs.add(href)

    return selected_hrefs


def fetch_and_save_article(url, output_folder):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        content = soup.find('div', id='bodyContent')
        if not content:
            logging.warning(f"No content found for URL: {url}")
            return

        header = soup.select('h1#firstHeading')[0].get_text() + "\n"
        collected_texts = [header]
        image_urls = []
        data = {"references": [], "external_links": []}

        header_tags = [f'h{i}' for i in range(1, 7)]
        content_tags = header_tags + ['p', 'img', 'a']

        # Extract text and images
        for element in content.find_all(content_tags):
            if element.name in header_tags + ['p']:
                text = element.get_text().replace('[edit]', '')
                collected_texts.append(text)
            elif element.name == 'img' and 'src' in element.attrs:
                src = element['src']
                full_image_url = 'https:' + \
                    src if src.startswith('//') else src
                image_urls.append(full_image_url)

        # Extract references
        ref_section = soup.find('ol', class_='references')
        if ref_section:
            for li in ref_section.find_all('li'):
                reference = li.get_text().strip()
                link = li.find('a', class_='external')
                if link and 'href' in link.attrs:
                    data["references"].append(
                        {"text": reference, "url": link['href']})

        # Extract external links directly without relying on the "External_links" span
        external_links = soup.find_all('a', class_=['external', 'text'])
        data["external_links"] = []  # Initialize the list for external links

        for link in external_links:
            if 'href' in link.attrs and 'rel' in link.attrs and 'nofollow' in link['rel']:
                link_data = {"text": link.get_text(), "url": link['href']}
                data["external_links"].append(link_data)

        article_text = '\n'.join(collected_texts)
        base_filename = safe_filename(url)

        # Define directories for different file types
        directories = {
            'text': 'text_files',
            'url': 'url_files',
            'imgs': 'image_files',
            'refs': 'reference_files',
            'html': 'html_files'
        }

        # Create directories if they don't exist
        for key, directory in directories.items():
            dir_path = os.path.join(output_folder, directory)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        # Prepare file paths within their respective directories
        text_filepath = os.path.join(
            output_folder, directories['text'], base_filename + '.txt')
        url_filepath = os.path.join(
            output_folder, directories['url'], base_filename + '.url')
        imgs_filepath = os.path.join(
            output_folder, directories['imgs'], base_filename + '.imgs')
        refs_filepath = os.path.join(
            output_folder, directories['refs'], base_filename + '.json')
        html_filepath = os.path.join(
            output_folder, directories['html'], base_filename + '.html')

        # Save all files
        with open(text_filepath, 'w') as f:
            f.write(article_text)
        with open(url_filepath, 'w') as f:
            f.write(url)
        with open(imgs_filepath, 'w') as f:
            json.dump(image_urls, f, indent=4)
        with open(refs_filepath, 'w') as f:
            json.dump(data, f, indent=4)
        with open(html_filepath, 'w') as f:
            f.write(soup.prettify())

        logging.info(f"Processed and saved files for URL: {url}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")


if __name__ == "__main__":
    config = get_config()

    download_path = config['rag_files_path']
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    main_listing_url = 'https://en.wikipedia.org/wiki/List_of_Art_Deco_architecture_in_the_United_States'
    main_listing_title = 'List of Art Deco architecture in the United States'

    lists = [main_listing_title]
    list_urls = [main_listing_url]

    listings = get_listing_pages(main_listing_url)
    building_urls1 = get_buildings_from_main_page(main_listing_url)
    building_urls2 = get_buildings_from_listing_pages(listings)
    buildings = set(building_urls1).union(building_urls2)
    pbar = tqdm(total=len(buildings), desc="Starting processing",
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}')
    for building in buildings:
        pbar.set_postfix_str(f"Processing URL: {building}")
        fetch_and_save_article(
            urljoin(wikipedia_base_url, building), download_path)
        pbar.update(1)
    pbar.close()
    print('All articles have been processed and saved.')
