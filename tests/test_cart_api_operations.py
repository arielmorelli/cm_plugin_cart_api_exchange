from cm_plugin_cart_api_exchange.cart_api_operations import chunk_dict, ExchangeApi

from mock import MagicMock, ANY
import unittest


class TestChunkList(unittest.TestCase):
    def test_chunk_dict_empty_list(self):
        test_dict = {}
        expected_restult = []

        chunked_lists = [c for c in chunk_dict(test_dict, size=10)]
        assert len(chunked_lists) == 0
        

    def test_chunk_dict_less_than_size(self):
        test_dict = {1: {'a': 'a'}, 2: {'b': 'b'}, 3: {'c': 'c'}}

        chunked_lists = [c for c in chunk_dict(test_dict, size=10)]
        assert len(chunked_lists) == 1
        assert len(chunked_lists[0]) == 3
        found = False
        for item in chunked_lists[0]:
            if item == test_dict[1]:
                found = True
                break
        for item in chunked_lists[0]:
            if item == test_dict[2]:
                found = found and True
                break
        for item in chunked_lists[0]:
            if item == test_dict[3]:
                found = found and True
                break
            
        assert found

    def test_chunk_dict_chunking_list(self):
        test_dict = {1: {'a': 'a'}, 2: {'b': 'b'}, 3: {'c': 'c'}}

        chunked_lists = [c for c in chunk_dict(test_dict, size=2)]
        assert len(chunked_lists) == 2
        assert len(chunked_lists[0]) == 2
        assert len(chunked_lists[1]) == 1

class TestExchangeApi(unittest.TestCase):
    def test_send_items(self):
        exchange_api = ExchangeApi("user", "password")
        exchange_api._make_patch_request = MagicMock()

        # empty items
        items = {}
        exchange_api.send_items("a-url", items, "cart-name")
        exchange_api._make_patch_request.assert_not_called()

        # 1 item
        url = "a-url"
        cart_name = "a-simple-cart"
        copies = 10
        exchange_api._make_patch_request.reset_mock()
        items = {1161: {"identifier": "1231231231231", "copies": copies}}

        exchange_api.send_items(url, items, cart_name)
        
        assert exchange_api._make_patch_request.call_count == 1
        called_url, called_data = exchange_api._make_patch_request.call_args[0]
        assert called_url == url
        assert called_data["name"] == cart_name
        assert called_data["total"]["copies"] == copies
        assert len(called_data["items"]) == len(items)

        # chunked items
        exchange_api._make_patch_request.reset_mock()
        items = {
            1161: {"identifier": "1231231231231", "copies": 1},
            1162: {"identifier": "1222222222211", "copies": 3},
            1163: {"identifier": "1233333333331", "copies": 2},
        }
        exchange_api.send_items("a-url", items, "cart-name", 2)
        assert exchange_api._make_patch_request.call_count == 2

        # Items with error
        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {"items": {"id": 1, "error": "a-error"}}

        exchange_api._make_patch_request.reset_mock()
        exchange_api._make_patch_request.return_value = MockResponse()
        items = {
            1161: {"identifier": "1231231231231", "copies": 1},
        }
        exchange_api.send_items("a-url", items, "cart-name", 2)
        assert exchange_api._make_patch_request.call_count == 1
