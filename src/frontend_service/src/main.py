from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import traceback
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import threading
import time

load_dotenv()
print("printing fe")

SERVER_HOST = os.environ['SERVER_HOST']
SERVER_PORT = int(os.environ['SERVER_PORT'])
CATALOG_SERVICE_URL = os.environ['CATALOG_SERVICE_URL']
CACHE_SIZE = int(os.environ['CACHE_SIZE']) 

REPLICAS = [
    {"id": int(os.environ['REPLICA_1_ID']), "url": os.environ['REPLICA_1_URL']},
    {"id": int(os.environ['REPLICA_2_ID']), "url": os.environ['REPLICA_2_URL']},
    {"id": int(os.environ['REPLICA_3_ID']), "url": os.environ['REPLICA_3_URL']},
]


# using python's ThreadPoolExecutor to handle multiple clients concurrently
MAX_WORKERS = 5
LOG_FILE = "/app/data/CACHE_ACTIVITY.log"
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

class LRUCache:
    def __init__(self, capacity, log_file):
        self.capacity = capacity
        self.cache = {}         
        self.usage_order = [] 
        self.lock = threading.Lock()
        self.log_file = log_file

    def _log(self, message):
        #get timestamp and log it to a file
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        # with open(self.log_file, "a") as f:
        #     f.write(f"[{timestamp}] {message}\n")
        
    def get(self, key):
        with self.lock:
            if key in self.cache:
                self.usage_order.remove(key)
                self.usage_order.append(key)
                self._log(f"CACHE HIT: {key}")
                return self.cache[key]
            else:
                self._log(f"CACHE MISS: {key}")
        return None

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self._log(f"CACHE UPDATE: {key}")
                self.cache[key] = value
                self.usage_order.remove(key)
                self.usage_order.append(key)
            else:
                # New key
                if len(self.cache) >= self.capacity:
                    self._log(f"CACHE EVICT: {key}")
                    oldest_key = self.usage_order.pop(0)
                    del self.cache[oldest_key]

                self._log(f"CACHE INSERT: {key}")
                self.cache[key] = value
                self.usage_order.append(key)

    def invalidate(self, key):
        with self.lock:
            if key in self.cache:
                self._log(f"CACHE EVICT: {key}")
                self.usage_order.remove(key)
                del self.cache[key]


cache = LRUCache(CACHE_SIZE, LOG_FILE)

leader = None

# Monitor the leader status in a separate thread
def monitor_leader():
    while True:
        time.sleep(5)
        if leader:
            try:
                res = requests.get(f"{leader['url']}/health", timeout=1)
                if res.status_code != 200:
                    raise Exception("Unhealthy")
            except:
                print("[MONITOR] Leader seems to be down. Re-electing...")
                select_leader()


def select_leader():
    global leader
    sorted_replicas = sorted(REPLICAS, key=lambda r: -r['id'])
    print(f"[INFO] Sorted replicas: {sorted_replicas}", flush=True)
    for replica in sorted_replicas:
        try:
            res = requests.get(f"{replica['url']}/health", timeout=1)
            if res.status_code == 200:
                leader = replica
                notify_all_replicas(replica['id'])
                print(f"[LEADER] Selected replica {replica['id']}", flush=True)
                return
        except:
            continue
    leader = None

def notify_all_replicas(leader_id):
    print("raching notify all replicas", flush=True)
    for r in REPLICAS:
        try:
            requests.post(f"{r['url']}/set_leader", json={"leader_id": leader_id})
        except:
            print(f"[WARN] Failed to notify replica {r['id']}")

select_leader()

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
        global leader
        if self.path.startswith('/stocks/without/cache/'):
            stock_name = self.path.split('/')[-1]
            try:
                cat_res = requests.get(f"{CATALOG_SERVICE_URL}/stocks/{stock_name}")
                print(f"[CATALOG] {cat_res.status_code} - {cat_res.text}")
                self._send_json_response(cat_res.status_code, cat_res.json())
            except Exception as e:
                print("[ERROR] Catalog request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
                return
            
        elif self.path.startswith('/stocks/'):
            stock_name = self.path.split('/')[-1]
            # start_time = time.time()
            try:
                cached_stcok = cache.get(stock_name)
                if cached_stcok:
                    print(f"[CACHE HIT] {cached_stcok}")
                    self._send_json_response(200, cached_stcok)
                    return
                else:
                    try:
                        cat_res = requests.get(f"{CATALOG_SERVICE_URL}/stocks/{stock_name}")
                        print(f"[CATALOG] {cat_res.status_code} - {cat_res.text}")
                        if cat_res.status_code == 200:
                            cache.put(stock_name, cat_res.json())
                        self._send_json_response(cat_res.status_code, cat_res.json())
                    except Exception as e:
                        print("[ERROR] Catalog request failed:", e)
                        traceback.print_exc()
                        self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
                        return
            except Exception as e:
                print("[ERROR] Frontend request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
                return
            
        elif self.path == '/orders':
            # GET /orders
            # returns a list of orders
            # or {'error': {'code': xx, 'message': 'error message'}}

            try:
                if not leader:
                    select_leader()
                
                if not leader:
                    self._send_json_response(503, {"error": {"code": 503, "message": "No leader available"}})
                    return

                print(f"[LEADER] {leader['id']}", flush=True)
                order_res = requests.get(f"{leader['url']}/orders", timeout=2)
                print(f"[ORDER] {order_res.status_code} - {order_res.text}", flush=True)
                self._send_json_response(order_res.status_code, order_res.json())
            except:
                print("[ERROR] Leader down, retrying...")
                select_leader()
                self._send_json_response(503, {"error": {"code": 503, "message": "Leader unavailable, please retry"}})
                return

            print(f"[ORDER] {order_res.status_code} - {order_res.text}")
            self._send_json_response(order_res.status_code, order_res.json())

        # returns {'data': {'number': 1, 'name': 'AAPL', 'type': 'buy', 'quantity': 10}}
        # or {'error': {'code': xx, 'message': 'error message'}}
        elif self.path.startswith('/orders/'):
            order_number = self.path.split('/')[-1]
            try:
                
                if not leader:
                    select_leader()
                if not leader:
                    self._send_json_response(503, {"error": {"code": 503, "message": "No leader available"}})
                    return

                try:
                    order_res = requests.get(f"{leader['url']}/orders/{order_number}", timeout=2)
                    self._send_json_response(order_res.status_code, order_res.json())
                except:
                    print("[ERROR] Leader down, retrying...")
                    select_leader()
                    self._send_json_response(503, {"error": {"code": 503, "message": "Leader unavailable, please retry"}})
                    return

                print(f"[ORDER] {order_res.status_code} - {order_res.text}")
                self._send_json_response(order_res.status_code, order_res.json())
            except Exception as e:
                print("[ERROR] Order request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
        else:
            self._send_json_response(404, {"error":  {"code": 404, "message":"URL not found"}})

    def do_POST(self):
        global leader
        if self.path == '/orders':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                data = json.loads(self.rfile.read(content_length).decode())
            except Exception as e:
                print("[ERROR] Invalid JSON body:", e)
                self._send_json_response(400, {"error": {"code": 400, "message":"Invalid JSON"}})
                return

            try:
                
                if not leader:
                    select_leader()
                if not leader:
                    self._send_json_response(503, {"error": {"code": 503, "message": "No leader available"}})
                    return

                # propagate follower URLs in request
                followers = [r['url'] for r in REPLICAS if r['id'] != leader['id']]
                payload = data.copy()
                payload["followers"] = followers

                try:
                    print("reached here you predicted correct")
                    order_res = requests.post(f"{leader['url']}/orders", json=payload, timeout=2)
                    self._send_json_response(order_res.status_code, order_res.json())
                except:
                    print("[ERROR] Leader down during trade, retrying...")
                    traceback.print_exc()
                    select_leader()
                    self._send_json_response(503, {"error": {"code": 503, "message": "Leader unavailable, please retry"}})


                self._send_json_response(order_res.status_code, order_res.json())
            except Exception as e:
                print("[ERROR] Order request failed:", e)
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal server error"}})
        elif self.path.startswith('/invalidate'):
            stock_name = self.path.split('/')[-1]
            print(f"[INVALIDATE] Request received for {stock_name}", flush=True)
            cache.invalidate(stock_name)
            self._send_json_response(200, {"success": True})
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
    #uncomment this line for paxos
    # threading.Thread(target=monitor_leader, daemon=True).start()
