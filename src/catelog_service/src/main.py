from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
import json
import csv
import os
import threading
import time
import traceback
from dotenv import load_dotenv

load_dotenv()


CATALOG_FILE = os.environ['CATALOG_FILE']
HOST = os.environ['CATALOG_HOST']
PORT = int(os.environ['CATALOG_PORT'])

# Global in-memory catalog
# catalog = {
#     'x': {'price': a, 'quantity': b},
#   }
# x -> str, a -> float, b -> int
catalog = {}  

catalog_lock = threading.Lock()
SAVE_INTERVAL = 10  # seconds between periodic saves

# this helps to initialize the catalog with some default values if the file is not present
def initialize_catalog_data():
    global catalog
    with catalog_lock:
        catalog = {
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
            },
            "SwordCo": {
                "price": 25.00,
                "quantity": 100
            },
            "ShieldCo": {
                "price": 30.00,
                "quantity": 100
            },
            "BowCo": {
                "price": 35.00,
                "quantity": 100
            },
            "ArrowCo": {
                "price": 2.50,
                "quantity": 100
            },
            "PotionCo": {
                "price": 10.00,
                "quantity": 100
            },
            "HelmetCo": {
                "price": 15.00,
                "quantity": 100
            },
        }
    print("[INIT] Default catalog initialized in memory")


# Load catalog from CSV once at startup
def load_catalog():
    global catalog
    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                catalog[row['name']] = {
                    'price': float(row['price']),
                    'quantity': int(row['quantity'])
                }
    print(f"[INIT] Catalog loaded into memory: {catalog}")

# Periodically save catalog to disk every 10 secs
def periodic_save():
    while True:
        time.sleep(SAVE_INTERVAL)
        with catalog_lock:
            with open(CATALOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'price', 'quantity'])
                for name, data in catalog.items():
                    writer.writerow([name, data['price'], data['quantity']])
        print(f"Catelog saved to disk at {time.ctime()}")

class CatalogHandler(BaseHTTPRequestHandler):

    def _send_json_response(self, code, payload):
        body = json.dumps(payload)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        # print(body)
        self.wfile.write(body.encode())

    def get_stocks_process(self, stock_name):
        with catalog_lock:
            if stock_name in catalog:
                self._send_json_response(200, {"data": {"name": stock_name, "price": catalog[stock_name]["price"], "quantity": catalog[stock_name]["quantity"]}})
                return
            else:
                self._send_json_response(404, {"error": {"code": 404, "message":"stock not found"}})
                return

    # GET /lookup/{stock_name}
    def do_GET(self):
        if self.path.startswith("/stocks/"):
            stock_name = self.path.split('/')[-1]
            self.get_stocks_process(stock_name)
        else:
            self._send_json_response(404, {"error": {"code": 404,"message":"invalid endpoint"}})

    def input_stock_change_validation(self, change_str):
        try:
            change = int(change_str)
        except ValueError:    
            self._send_json_response(400, {"error": {"code": 400, "message":"invalid quantity"}})
            return False, None
        
        return True, change

    def update_stocks_process(self, stock_name, change_str):
        try:
            valid, res = self.input_stock_change_validation(change_str)
            if not valid:
                return res
            
            change = res
            with catalog_lock:
                if stock_name in catalog:
                    new_qty = catalog[stock_name]['quantity'] + change
                    if new_qty < 0:
                        self._send_json_response(400, {"error": {"code": 400, "message":"Insufficient stock"}})
                        return
                    catalog[stock_name]['quantity'] = new_qty
                    self._send_json_response(200, {"success": True})
                    return
                else:
                    self._send_json_response(404, {"error": {"code": 404, "message":"stock not found"}})

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._send_json_response(500, {"error": {"code": 500, "message":"internal server error"}})
            return

    # POST /update/{stock_name}/{change}
    def do_POST(self):
        print("reached catalog service -  ", self.path)
        if self.path.startswith("/update/"):
            parts = self.path.strip('/').split('/')
            if len(parts) == 3:
                _, stock_name, change_str = parts
                self.update_stocks_process(stock_name, change_str)
            else:
                self._send_json_response(400, {"error": {"code": 400, "message":"invalid update path"}})
        else:
            self._send_json_response(404, {"error": {"code": 404, "message":"invalid endpoint"}})

def run():
    if os.path.exists(CATALOG_FILE):
        load_catalog()
    else:
        initialize_catalog_data()

    threading.Thread(target=periodic_save, daemon=True).start()  # Background disk sync

    executor = ThreadPoolExecutor(max_workers=5)
    server = HTTPServer((HOST, PORT), CatalogHandler)
    print(f"Catalog Service running on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server.get_request()
            executor.submit(server.process_request, client_socket, client_address)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down server...")
        executor.shutdown(wait=True)
        server.server_close()

if __name__ == '__main__':
    run()
