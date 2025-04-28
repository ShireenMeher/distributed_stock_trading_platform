import unittest
from unittest.mock import patch, MagicMock
import os
import threading
import time
import csv
import traceback
from dotenv import load_dotenv
from main import CatalogHandler 


load_dotenv()
test_catalog_lock = threading.Lock()
test_catalog = {
            "GameStart": {
                "price": 15.99,
                "quantity": 100
            },
            "RottenFishCo": {
                "price": 5.49,
                "quantity": 100
            },
            "BoarCo": {
                "price": 9.99,
                "quantity": 100
            },
            "MenhirCo": {
                "price": 12.75,
                "quantity": 100
            }
        }

TEST_CATALOG_FILE = os.environ['TEST_CATALOG_FILE']


class TestCatalogHandler(unittest.TestCase):

    def test_input_stock_change_validation_valid(self):
        handler = CatalogHandler.__new__(CatalogHandler)  
        handler._send_json_response = MagicMock() 
        is_valid, value = handler.input_stock_change_validation("10")
        self.assertTrue(is_valid)
        self.assertEqual(value, 10)

    def test_input_stock_change_validation_invalid(self):
        handler = CatalogHandler.__new__(CatalogHandler)
        handler._send_json_response = MagicMock()
        is_valid, value = handler.input_stock_change_validation("abc")
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        handler._send_json_response.assert_called_once_with(400, {'error': {'code': 400, 'message': 'invalid quantity'}})

    @patch("main.catalog", test_catalog)
    def test_update_stock_quantity_insufficient(self):
        # Setup dummy handler with mocked response method
        with test_catalog_lock:
            test_catalog["GameStart"]["quantity"] = 100
        handler = CatalogHandler.__new__(CatalogHandler)
        handler._send_json_response = MagicMock()
        stock_name = "GameStart"
        new_quantity = -110  # too much, should trigger error
        handler.update_stocks_process(stock_name, str(new_quantity))
        handler._send_json_response.assert_called_once_with(400,{'error': {'code': 400, 'message': 'Insufficient stock'}})


if __name__ == "__main__":
    unittest.main()