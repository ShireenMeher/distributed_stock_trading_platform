from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import traceback
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

SERVER_HOST = os.environ['SERVER_HOST']
SERVER_PORT = int(os.environ['SERVER_PORT'])
CATALOG_SERVICE_URL = os.environ['CATALOG_SERVICE_URL']
ORDER_SERVICE_URL = os.environ['ORDER_SERVICE_URL']

# using python's ThreadPoolExecutor to handle multiple clients concurrently
MAX_WORKERS = 5
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

class FrontendHandler(BaseHTTPRequestHandler):

    # This method is called when the server receives a request thats not allowed
    def _handle_not_allowed(self):
        self._send_json_response(405, {"error": {"code": 405, "message": "Method not allowed"}})


    #BEGIN AI CODE: ChatGPT.PROMPT: Give me a function to send a JSON response for http requests
    def _send_json_response(self, code, payload):
        body = json.dumps(payload)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    #BEGIN AI CODE: ChatGPT.PROMPT: Give me a function to send a JSON response for http requests

    def do_PUT(self):
        self._handle_not_allowed()

    def do_PATCH(self):
        self._handle_not_allowed()

    def do_DELETE(self):
        self._handle_not_allowed()

    def do_HEAD(self):
        self._handle_not_allowed()

    def do_OPTIONS(self):
        self._handle_not_allowed()

    def do_GET(self):
        if self.path.startswith('/stocks/'):
            stock_name = self.path.split('/')[-1]
            try:
                cat_res = requests.get(f"{CATALOG_SERVICE_URL}/stocks/{stock_name}")
                print(f"[CATALOG] {cat_res.status_code} - {cat_res.text}")
                self._send_json_response(cat_res.status_code, cat_res.json())
            except Exception as e:
                print("[ERROR] Catalog request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})

        # returns {'data': {'number': 1, 'name': 'AAPL', 'type': 'buy', 'quantity': 10}}
        # or {'error': {'code': xx, 'message': 'error message'}}
        elif self.path.startswith('/orders/'):
            order_number = self.path.split('/')[-1]
            try:
                order_res = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_number}")
                print(f"[ORDER] {order_res.status_code} - {order_res.text}")
                self._send_json_response(order_res.status_code, order_res.json())
            except Exception as e:
                print("[ERROR] Order request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
        else:
            self._send_json_response(404, {"error":  {"code": 404, "message":"URL not found"}})

    def do_POST(self):
        if self.path == '/orders':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                data = json.loads(self.rfile.read(content_length).decode())
            except Exception as e:
                print("[ERROR] Invalid JSON body:", e)
                self._send_json_response(400, {"error": {"code": 400, "message":"Invalid JSON"}})
                return

            try:
                order_res = requests.post(f"{ORDER_SERVICE_URL}/orders", json=data)
                self._send_json_response(order_res.status_code, order_res.json())
            except Exception as e:
                print("[ERROR] Order request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
        else:
            self._send_json_response(404, {"error": {"code": 404, "message":"URL not found"}})

def start_server():
    executor = ThreadPoolExecutor(max_workers=5)
    server = HTTPServer((SERVER_HOST, SERVER_PORT), FrontendHandler)
    print(f"Frontend Service running on {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            client_socket, client_address = server.get_request()
            executor.submit(server.process_request, client_socket, client_address)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down server...")
        executor.shutdown(wait=True)
        server.server_close()

if __name__ == '__main__':
    start_server()
