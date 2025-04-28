import unittest
from unittest.mock import patch, MagicMock
from main import FrontendHandler
from io import BytesIO

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
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler._send_json_response = FrontendHandler._send_json_response.__get__(handler)
        return handler
    
# BEGIN AI CODE: ChatGPT.PROMPT: Give me DummyRequest class is used to simulate HTTP requests for testing purposes

class TestFrontendHandler(unittest.TestCase):

    @patch('main.requests.get')
    def test_lookup_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"price": 10.0, "quantity": 100}
        mock_get.return_value.text = '{"price": 10.0, "quantity": 100}'
        req = DummyRequest(method="GET", path="/lookup/GameStart")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn('"price": 10.0', response)
        self.assertIn('"quantity": 100', response)

    @patch('main.requests.get')
    def test_lookup_failure(self, mock_get):
        mock_get.side_effect = Exception("service down")
        req = DummyRequest(method="GET", path="/lookup/GameStart")
        handler = req.make_handler()
        handler.do_GET()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn("Internal server error", response)

    @patch('main.requests.post')
    def test_trade_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        headers = {'Content-Length': '22'}
        body = '{"stock": "GameStart"}'
        req = DummyRequest(method="POST", path="/trade", headers=headers, body=body)
        handler = req.make_handler()
        handler.do_POST()
        req.wfile.seek(0)
        response = req.wfile.read().decode()
        self.assertIn('"success": true', response)

    # def test_trade_invalid_json(self):
    #     headers = {'Content-Length': '10'}
    #     body = 'invalid-json'
    #     req = DummyRequest(method="POST", path="/trade", headers=headers, body=body)
    #     handler = req.make_handler()
    #     handler.do_POST()
    #     req.wfile.seek(0)
    #     response = req.wfile.read().decode()
    #     self.assertIn("Invalid JSON", response)

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
    unittest.main()
