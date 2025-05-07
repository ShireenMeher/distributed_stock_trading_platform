import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from main import OrderHandler, orders_data, order_lock
import json

class DummyRequest:
    def __init__(self, method="POST", path="/orders", headers=None, body=None):
        self.command = method
        self.path = path
        self.headers = headers or {}
        self.rfile = BytesIO(body.encode() if body else b"")
        self.wfile = BytesIO()

    def make_handler(self):
        handler = OrderHandler.__new__(OrderHandler)
        handler.command = self.command
        handler.path = self.path
        handler.headers = self.headers
        handler.rfile = self.rfile
        handler.wfile = self.wfile
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler._send_json_response = OrderHandler._send_json_response.__get__(handler)
        return handler

class TestOrderHandler(unittest.TestCase):

    def setUp(self):
        with order_lock:
            orders_data.clear()

    def test_get_existing_order(self):
        with order_lock:
            orders_data[1] = {'name': 'TestStock', 'type': 'buy', 'quantity': 10}
        req = DummyRequest(method="GET", path="/orders/1")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn('"name": "TestStock"', response)

    def test_get_nonexistent_order(self):
        req = DummyRequest(method="GET", path="/orders/999")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("order not found", response)

    def test_health_check(self):
        req = DummyRequest(method="GET", path="/health")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn('"status": "alive"', response)

    def test_sync_missing(self):
        with order_lock:
            orders_data[1] = {'name': 'A', 'type': 'buy', 'quantity': 1}
            orders_data[2] = {'name': 'B', 'type': 'sell', 'quantity': 2}
        req = DummyRequest(method="GET", path="/sync_missing?from_id=1")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn('"transaction_number": 2', response)

    def test_set_leader(self):
        headers = {'Content-Length': '18'}
        body = '{"leader_id": 3}'
        req = DummyRequest(method="POST", path="/set_leader", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn('"success": true', response)


    @patch("main.requests.post")
    def test_valid_trade_request_buy(self, mock_catalog_post):
        mock_catalog_post.return_value.status_code = 200
        mock_catalog_post.return_value.json.return_value = {"success": True}
        headers = {'Content-Length': '61'}
        body = '{"name": "GameStart", "quantity": 2, "type": "buy"}'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("transaction_number", response)
        self.assertEqual(mock_catalog_post.call_count, 1)

    @patch("main.requests.post")
    def test_valid_trade_request_sell(self, mock_catalog_post):
        mock_catalog_post.return_value.status_code = 200
        mock_catalog_post.return_value.json.return_value = {"success": True}
        headers = {'Content-Length': '61'}
        body = '{"name": "BoarCo", "quantity": 5, "type": "sell"}'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("transaction_number", response)

    # def test_invalid_endpoint(self):
    #     headers = {'Content-Length': '61'}
    #     body = '{"name": "GameStart", "quantity": 2, "type": "buy"}'
    #     req = DummyRequest(method="POST", path="/wrong-endpoint", headers=headers, body=body)
    #     handler = req.make_handler()
    #     handler.do_POST()
    #     req.wfile.seek(0)
    #     response = req.wfile.read().decode()
    #     self.assertIn("Invalid endpoint", response)


    @patch("main.requests.post")
    def test_invalid_fields(self, mock_catalog_post):
        headers = {'Content-Length': '45'}
        body = '{"name": "", "quantity": 0, "type": "hold"}'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler._send_json_response = MagicMock()
        handler.do_POST()
        handler._send_json_response.assert_called_once_with(400, {'error': {'code': 400, 'message': 'Invalid JSON or fields'}})

    @patch("main.requests.post")
    def test_catalog_update_failure(self, mock_catalog_post):
        mock_catalog_post.return_value.status_code = 400
        mock_catalog_post.return_value.json.return_value = {"error": "Insufficient stock"}
        headers = {'Content-Length': '61'}
        body = '{"name": "GameStart", "quantity": 2000, "type": "buy"}'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("Insufficient stock", response)


if __name__ == "__main__":
    unittest.main()
