from bs4 import BeautifulSoup
from unicodedata import normalize

class EcommerceSoupParser:
    _normalization_required = {
        'uae.amazon.com', 
        'www.amazon.ae', 
        'www.noon.com',
    }

    __price_selectors = {
        'uae.amazon.com': 'span#price_inside_buybox',
        'uae.microless.com': 'div.the-price span.product-price',
        'www.amazon.ae': 'span#price_inside_buybox',
        'gear-up.me': 'span.price 5',
        'www.noon.com': '[data-qa=div-price-now]',
        'www.newegg.com': 'div.price-current strong',
        'uaegamers.ae': 'span.woocommerce-Price-amount.amount.bdi',
    }

    __outofstock_selectors = {
        'uae.microless.com': 'div.out-of-stock-label',
        'www.noon.com': 'div.sc-1xw7r3i-0.grpnyI',
        'gear-up.me': 'div.bundle_product_stock p.availability.out-of-stock',
        'uaegamers.ae': '[data-class=out-of-stock]',
    }

    def __init__(self, html, host):
        self.soup = BeautifulSoup(html, 'html.parser')
        self.host = host

    def get_price(self):
        selector = self.__price_selectors.get(self.host)
        if not selector:
            return

        price_elem = self.soup.select_one(selector)
        if price_elem:
            price_str = self._handle_elem_data(price_elem.get_text())
            price = filter(lambda c: c.isdigit() or c in '.' , price_str)
            return ''.join(price)

        return

    def get_outofstock_status(self):
        selector = self.__outofstock_selectors.get(self.host)
        if not selector:
            return
    
        outofstock_elem = self.soup.select_one(selector)
        return outofstock_elem is not None

    def _handle_elem_data(self, data):
        if self.host in self._normalization_required:
            return normalize("NFKD", data)
        else:
            return data