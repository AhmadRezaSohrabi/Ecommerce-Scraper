


def get_products(api):
    page = 1
    products = []
    while True:
        print(page)
        page_products = api.get("products", params={"per_page": 50, "page": page}).json()
        products += page_products
        if not page_products:
            break
        page += 1
    return products