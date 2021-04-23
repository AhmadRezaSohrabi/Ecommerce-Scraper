from unicodedata import normalize
from html.parser import HTMLParser


class EcommerceHTMLParser(HTMLParser):
    __price_props = {
        'uae.amazon.com': {'tag': 'span', 'attr': 'id', 'value': 'price_inside_buybox'},
        'uae.microless.com': {'tag': 'span', 'attr': 'class', 'value': 'the-price'},
        'www.amazon.ae': {'tag': 'span', 'attr': 'id', 'value': 'price_inside_buybox'},
        'gear-up.me': {'tag': 'span', 'attr': 'class', 'value': 'price 5'},
        'www.noon.com': {'tag': 'div', 'attr': 'data-qa', 'value': 'div-price-now'},
    }

    __out_of_stock_props = {
        'uae.microless.com': {'tag': 'div', 'attr': 'class', 'value': 'out-of-stock-label'},
        'www.noon.com': {'tag': 'div', 'attr': 'class', 'value': 'sc-1xw7r3i-0'},
        'gear-up.me': {'tag': 'p', 'attr': 'class', 'value': 'out-of-stock'},
    }
    def __init__(self, host):
        super(EcommerceHTMLParser, self).__init__()
        self.host = host
        self.is_price_tag = False
        self.out_of_stock = False
        self.price = None

    def handle_starttag(self, tag, attrs):
        # Price parser
        host_price_props = self.__price_props.get(self.host)
        if host_price_props is not None:
            if tag == host_price_props['tag']:
                for attr, value in attrs:
                    if host_price_props['attr'] == attr and host_price_props['value'] == value:
                        self.is_price_tag = True

        # Out of Stock parser
        host_out_of_stock_props = self.__out_of_stock_props.get(self.host)
        if host_out_of_stock_props is not None:
            if tag == host_out_of_stock_props['tag']:
                for attr, value in attrs:                    
                    if host_out_of_stock_props['attr'] == attr and host_out_of_stock_props['value'] in value:
                        self.out_of_stock = True

    def handle_endtag(self, tag):
        self.is_price_tag = False

    def handle_data(self, data):
        if self.is_price_tag:
            handle_method = self._get_handle_method()
            if handle_method:
                price_str = handle_method(data)
                if self.host == 'gear-up.me':
                    self.price = price_str[0]
                else:
                    self.price = price_str[1]
            else:
                self.price = data

    
    def _get_handle_method(self):
        if self.host in {'uae.amazon.com', 'www.amazon.ae', 'www.noon.com'}:
            return self._get_normalized_price
        return

    
    def _get_normalized_price(self, data):
        data = normalize("NFKD", data)
        price_str = data.strip().split(' ')
        return price_str