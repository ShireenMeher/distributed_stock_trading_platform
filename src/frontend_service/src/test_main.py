import unittest
from unittest.mock import patch, MagicMock
from main import FrontendHandler
from io import BytesIO
import json
import threading
import os
from flask import Flask, jsonify

mock_order_app = Flask(__name__)

@mock_order_app.route("/health", methods=["GET"])
def mock_health():
    return jsonify({"status": "alive"})

@mock_order_app.route("/orders", methods=["POST"])
def mock_orders():
    return jsonify({"data": {"transaction_number": 123}})

@mock_order_app.route("/update/<name>/<int:change>", methods=["POST"])
def mock_update(name, change):
    return jsonify({"success": True})

def run_mock(app, port):
    app.config['TESTING'] = True
    threading.Thread(target=app.run, kwargs={"port": port, "use_reloader": False}, daemon=True).start()

#BEGIN AI CODE: ChatGPT.PROMPT: Give me DummyRequest class is used to simulate HTTP requests for testing purposes

class DummyRequest:
    def __init__(self, method="GET", path="/", headers=None, body=None):
        self.command = method
        self.path = path
        self.headers = headers or {}
        self.rfile = BytesIO(body.encode() if body else b"")
        self.wfile = BytesIO()

    def make_handler(self):
        handler = FrontendHandler.__new__(FrontendHandler)
        handler.rfile = self.rfile
        handler.wfile = self.wfile
        handler.command = self.command
        handler.path = self.path
        handler.headers = self.headers
        handler.leader = {'id': 1, 'url': 'http://localhost:6001'}
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler._send_json_response = FrontendHandler._send_json_response.__get__(handler)
        return handler
    
# BEGIN AI CODE: ChatGPT.PROMPT: Give me DummyRequest class is used to simulate HTTP requests for testing purposes

class TestFrontendHandler(unittest.TestCase):

# BEGIN AI CODE: ChatGPT.PROMPT: Fix this test, mock it wherever necessary using Magicmock (copy pasted the code snippet in prompt)


    @patch('main.requests.get')
    @patch('main.requests.post')
    @patch.dict(os.environ, {
        "REPLICA_1_URL": "http://order_service_1:6001",
        "REPLICA_2_URL": "http://order_service_2:6002",
        "REPLICA_3_URL": "http://order_service_3:6003",
        "REPLICA_1_ID": "1",
        "REPLICA_2_ID": "2",
        "REPLICA_3_ID": "3",
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "5001",
        "CATALOG_SERVICE_URL": "http://localhost:5003",
        "CACHE_SIZE": "5"
    })
    def test_trade_with_followers(self, mock_post, mock_get):
        # Mock GET calls for /health
        def get_side_effect(url, *args, **kwargs):
            if url.endswith("/health"):
                return MagicMock(status_code=200, json=lambda: {"status": "alive"})
            elif url.endswith("/orders"):
                return MagicMock(
                    status_code=200,
                    json=lambda: {"data": {"transaction_number": 123}},
                    text='{"data": {"transaction_number": 123}}'
                )
            return MagicMock(status_code=404, json=lambda: {"error": "not found"})

        mock_get.side_effect = get_side_effect

        # Mock POST calls
        def post_side_effect(url, *args, **kwargs):
            if url.endswith("/orders"):
                return MagicMock(
                    status_code=200,
                    json=lambda: {"data": {"transaction_number": 123}},
                    text='{"data": {"transaction_number": 123}}'
                )
            elif "/update/" in url or "/propagate" in url:
                return MagicMock(status_code=200, json=lambda: {"success": True})
            return MagicMock(status_code=500, json=lambda: {"error": "unexpected"})

        mock_post.side_effect = post_side_effect

        # Simulate POST /orders
        headers = {'Content-Length': '96'}
        body = '{"name": "GameStart", "quantity": 2, "type": "buy", "followers": ["http://localhost:8002"]}'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()

        req.wfile.seek(0)
        response = req.wfile.read().decode()
        print("Test response:", response)
        self.assertIn("transaction_number", response)

# BEGIN AI CODE: ChatGPT.PROMPT: Fix this test, mock it wherever necessary using Magicmock (copy pasted the code snippet in prompt)

    @patch('main.requests.get')
    @patch('main.requests.post')
    def test_trade_success(self, mock_post, mock_get):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"data": {"transaction_number": 123}}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "alive"}

        headers = {'Content-Length': '54'}
        body = '{"name": "GameStart", "quantity": 1, "type": "buy"}'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("transaction_number", response)


    @patch('main.requests.get')
    def test_lookup_failure(self, mock_get):
        mock_get.side_effect = Exception("service down")
        req = DummyRequest(method="GET", path="/stocks/GameStart")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("Internal server error", response)

    def test_trade_invalid_json(self):
        headers = {'Content-Length': '10'}
        body = 'invalid-json'
        req = DummyRequest(method="POST", path="/orders", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("Invalid JSON", response)

    def test_get_invalid_url(self):
        req = DummyRequest(method="GET", path="/invalid")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("URL not found", response)

    def test_post_invalid_url(self):
        headers = {'Content-Length': '22'}
        body = '{"stock": "GameStart"}'
        req = DummyRequest(method="POST", path="/not-trade", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("URL not found", response)


if __name__ == '__main__':
    run_mock(mock_order_app, 5002)
    import time; time.sleep(3) 
    unittest.main()
