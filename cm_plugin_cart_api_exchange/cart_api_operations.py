import requests
import logging

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
            response = self._make_get_request(self.CREATE_CART_URI, request_body)
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
        total = 0
        total_with_error = 0
        current_chunk = 0
        for chunk in chunk_dict(items, chunk_size):
            current_chunk += 1
            total += len(chunk)
            request_body_as_dict = {
                "name": cart_name,
                "total": {
                    "items": len(chunk),
                    "copies": sum([item.get("copies", 0) for item in chunk]),
                },
                # "values": {
                #     "USD": sum([w.get("price", 0) for w in chunk]),
                # },
                "items": [self._items_to_api_request_entry(item)
                          for item in chunk],
            }
            try:
                response = self._make_patch_request(url, request_body_as_dict)
            except Exception as err:
                total_with_error += len(chunk)
                logging.warning("Error sending items. Chunk %d. %s", current_chunk, err)
                continue

            if response.status_code < 300:
                if "items" in response.json():
                    entries = response.json()
                    for entry in entries["items"]:
                        if "error" in entries["items"] and entries["items"]["error"]:
                            total_with_error += 1
            else:
                total_with_error += len(chunk)
                logging.error("Cannot send values. %d. %s", response.status_code, response.content)

        logging.info("Sent %d. %d with error.", total, total_with_error)


    def _make_get_request(self, url, data):
        headers = {
            "Content-Type": "application/json",
        }
        return requests.post(
            url, json=data, headers=headers,
            auth=HTTPBasicAuth(self.user, self.password)
        )

    def _make_patch_request(self, url, data):
        headers = {
            "Content-Type": "application/vnd.demarque.market.cart+json",
        }
        return requests.patch(
            url, json=data, headers=headers,
            auth=HTTPBasicAuth(self.user, self.password)
        )

