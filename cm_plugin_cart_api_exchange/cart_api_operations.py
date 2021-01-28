import requests

from requests.auth import HTTPBasicAuth


def chunk_dict(target, size):
    values = list(target.values())
    for n in range(0, len(values), size):
        yield values[n:size + n]


class ExchangeApi(object):
    CREATE_CART_URI = "https://market.feedbooks.com/carts"

    def __init__(self, user, password):
        self.user = user
        self.password = password
    
    def create_cart(self, cart_name):
        request_body = {
            "name": cart_name,
        }
        try:
            response = self._make_request(self.CREATE_CART_URI, request_body)
        except:
            raise
        
        try:
            return response.headers["Location"]
        except:
            raise Exception("Cannot create cart")

    @classmethod
    def _items_to_api_request_entry(cls, work):
        return {
            "id": work.get("identifier", ""),
            "quantity": work.get("copies", 0),
        }

    def send_items(self, url, items, cart_name, chunk_size=1000):
        for chunk in chunk_dict(items, chunk_size):
            request_body_as_dict = {
                "name": cart_name,
                "items": len(chunk),
                "copies": sum([item.get("copies", 0) for item in chunk]),
                # "values": {
                #     "USD": sum([w.get("price", 0) for w in chunk]),
                # },
                "items": [self._items_to_api_request_entry(item)
                          for item in chunk],
            }
            self._make_request(url, request_body_as_dict)

    def _make_request(self, url, data):
        headers = {
            "Content-Type": "application/json",
        }
        return self.requests.post(
            url, json=data, headers=headers,
            auth=HTTPBasicAuth(self.user, self.password)
        )

