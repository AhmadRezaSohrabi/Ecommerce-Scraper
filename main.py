import re
import json
import requests
from math import ceil


from sys import exit
from pprint import pprint

from urllib3.exceptions import InsecureRequestWarning


from woocommerce import API

from config import *

from ecommerce_scraper.utils import generate_csv, config_logger, print_progress_bar

from ecommerce_scraper.api import get_products
from ecommerce_scraper.html_parser import EcommerceHTMLParser
from ecommerce_scraper.soup import EcommerceSoupParser

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
root_logger = config_logger(__name__)
root_api = API(
    url=URL,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    version=API_VERSION,
    verify_ssl=False,
    timeout=120,
)

if __name__ == '__main__':
    # print('==> Fetching the products data ...', end=' ')
    # products = get_products(root_api)
    # print(f'Fetched --- Total = {len(products)}')


    # print('==> Storing fetched data ...', end=' ')
    # with open('products.json', 'w') as f:
    #     json.dump(products, f)

    # print('[ Backup ready. Moving on to next phase ]')

    print('==> Reading from fetched data ...', end=' ')
    with open('products.json', 'r') as f:
        products = json.load(f)

    harvested_info = []
    print('==> Processing data ...')
    for product in products:
        meta_data = product['meta_data']
        for md in meta_data:
            if md['key'] == '_alg_wc_internal_product_note':
                source_urls = [item['value'] for item in md['value']]
                harvested_info.append({
                    'id': product['id'],
                    'name': product['name'],
                    'source_urls': source_urls,
                })

    print('==> Scraping the urls for prices and tags ...')
    final_info = []
    not_updated_products = []
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    }
    harvested_info_count = len(harvested_info)
    print_progress_bar(0, harvested_info_count, prefix='Progress:', suffix='Complete', length=50)

    for i, product_info in enumerate(harvested_info):
        scraped_data = []
        failures = []
        name = product_info['name']
        print('[ Scraping ] --> ', name)
        urls = product_info['source_urls']
        for url in urls:
            try:
                res = requests.get(url, headers=headers, verify=False, timeout=60)
                if res:
                    page_html = res.content.decode('utf-8')
                    # parser = EcommerceHTMLParser(host=product_info['host'])
                    # parser.feed(page_html)
                
                    # if parser.price:
                    #     clean_price = ceil(float(parser.price.replace(',', '')))
                    # else:
                    #     clean_price = None
                    host = re.findall(r'https?://(.[^/]*)/', url)[0]

                    soup_parser = EcommerceSoupParser(html=page_html, host=host)

                    price = soup_parser.get_price()
                    if price:
                        clean_price = ceil(float(price))
                    else:
                        clean_price = None

                    scraped_data.append({
                        'price': clean_price,
                        'out_of_stock': soup_parser.get_outofstock_status(),
                    })

            except Exception as exc:
                if isinstance(exc, (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema)):
                    root_logger.warning('Invalid URL or Schema detected ==> {}\nProduct ==> {}'.format(url, name))
                    reason = 'Invalid URL or Schema'
                elif isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout)):
                    root_logger.warning('Time Out or Connection Error while connecting to ==> {}\nProduct ==> {}'.format(url, name))
                    reason = 'Time Out!'
                else:
                    root_logger.warning('Parser Error while scraping ==> {}\nProduct ==> {}'.format(url, name))
                    reason = 'Scraper not working!'
                
                failures.append({
                        'url': url,
                        'reason': reason
                })

        if scraped_data:
            scraped_prices = [item['price'] for item in scraped_data if not item['out_of_stock'] and item['price'] is not None]
            if all([item['out_of_stock'] for item in scraped_data]):
                final_info.append({
                    'id': product_info['id'],
                    'name': name,
                    'urls': urls,
                    'price': None,
                    'out_of_stock': True,
                })
            elif scraped_prices:
                final_info.append({
                    'id': product_info['id'],
                    'name': name,
                    'urls': urls,
                    'price': min(scraped_prices),
                    'out_of_stock': False,
                })

        for failure in failures:
            not_updated_products.append({
                'id': product_info['id'],
                'name': name,
                'urls': failure['url'],
                'reason': failure['reason']
            })
        print_progress_bar(i + 1, harvested_info_count, prefix='Progress:', suffix='Complete', length=50)


    print('==> Extracted price for {found_count} products.\n==> Price for {not_found_count} could not be extracted'.format(found_count=len(final_info), not_found_count=len(not_updated_products)))
    print('==> Generating CSV file base on extracted data ...')
    generate_csv(final_info, 'Scraped Products data')
    generate_csv(not_updated_products, 'Inaccessible Products data')
    print('==> Updating the prices based on the scraped data ...')
    exit('Done')
    for info in final_info:
        if info['out_of_stock'] == True:
            data = {
                "stock_status": "outofstock",
            }
            res = root_api.put("products/{}".format(info['id']), data)
        else:
            print('>>>> [{}]'.format(info['name']))
            data = {
                "meta_data": [
                    {
                        "key": "_mnswmc_regular_price",
                        "value": info['price'],
                    }
                ],
                "stock_status": "instock",
            }
            res = root_api.put("products/{}".format(info['id']), data)