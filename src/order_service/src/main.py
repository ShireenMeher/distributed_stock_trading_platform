from http.server import BaseHTTPRequestHandler, HTTPServer
from concurrent.futures import ThreadPoolExecutor
import json
import csv
import os
import threading
import requests
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

ORDER_FILE = os.environ['ORDER_FILE']
CATALOG_BASE_URL = os.environ['CATELOG_BASE_URL']
ORDER_HOST = os.environ['ORDER_HOST']
ORDER_PORT = int(os.environ['ORDER_PORT'])

TRANSACTION_ID = 0
transaction_lock = threading.Lock()
order_lock = threading.Lock()
SAVE_INTERVAL = 10  # seconds between periodic saves
REPLICA_SYNC_INTERVAL = 2 # seconds between sync with peers
print("this is a print statement")
# in memory order db
# transaction_number, name, type, quantity
# { 1: {'name': 'GameStart', 'type': 'buy', 'quantity': 2} }
orders_data = {} 

def periodic_save_to_disk():
    while True:
        time.sleep(SAVE_INTERVAL)
        with order_lock:
            with open(ORDER_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['transaction_number', 'name', 'type', 'quantity'])
                for txn_id, data in orders_data.items():
                    writer.writerow([txn_id, data['name'], data['type'], data['quantity']])
        print("[SYNC] Orders saved to disk.")

def load_orders_from_disk():
    global orders_data, TRANSACTION_ID

    # create file if not exists
    if not os.path.exists(ORDER_FILE):
        os.makedirs(os.path.dirname(ORDER_FILE), exist_ok=True)
        with open(ORDER_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['transaction_number', 'name', 'type', 'quantity'])

    # load orders from file & get max transaction id
    with open(ORDER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            txn = int(row['transaction_number'])
            orders_data[txn] = {
                'name': row['name'],
                'name': row['name'],
                'type': row['type'],
                'quantity': int(row['quantity'])
            }
        TRANSACTION_ID = max(orders_data.keys(), default=0)
    print(f"[INIT] Orders loaded: {orders_data}")

LEADER_ID = None

class OrderHandler(BaseHTTPRequestHandler):

    # This method is called when the server receives a request thats not allowed
    def _handle_not_allowed(self):
        self._send_json_response(405, {"error": {"code": 405, "message": "Method not allowed"}})

    # returns json response with status code directly to client (here frontend_service)
    def _send_json_response(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def update_request_input_validation(self, body):
        try:
            name = body["name"]
            if not name :
                raise ValueError    
            qty = int(body["quantity"])
            if qty <= 0:
                raise ValueError
            trade_type = body["type"]
            if trade_type not in ["buy", "sell"]:
                raise ValueError
            print("no validation error", flush=True)
            return True
        except:
            self._send_json_response(400, {"error": {"code": 400, "message":"Invalid JSON or fields"}})
            return False
        
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
        if self.path.startswith("/orders/"):
            try:
                order_number = self.path.split('/')[-1]
                with order_lock:
                    if int(order_number) in orders_data:
                        self._send_json_response(200, {"data": orders_data[int(order_number)]})
                        return
                    else:
                        self._send_json_response(404, {"error": {"code": 404, "message":"order not found"}})
                        return
            except ValueError:
                self._send_json_response(500, {"error": {"code": 400, "message":"Internal server error"}})
                return
            
        elif self.path == "/health":
            alive_status = {"status": "alive"}
            self._send_json_response(200, alive_status)

        # this route /sync_missing/?from_id=1 is used to sync orders with followers
        # it returns all orders with txn_id > from_id
        # for example, if from_id = 1, it returns all orders with txn_id > 1
        # this is used when a follower starts up and needs to sync with the leader
        elif self.path.startswith("/sync_missing"):
            from_id = int(self.path.split("=")[-1])
            result = []
            with order_lock:
                for txn, data in orders_data.items():
                    if txn > from_id:
                        result.append({
                            "transaction_number": txn,
                            "name": data["name"],
                            "type": data["type"],
                            "quantity": data["quantity"]
                        })
            self._send_json_response(200, {"data": result})
        
        elif self.path == "/orders":
            # this is used to get all orders
            # it returns all orders in the format:
            # [
            #     {
            #         "transaction_number": 1,
            #         "name": "GameStart",
            #         "type": "buy",
            #         "quantity": 2
            #     },
            # ]
            result = {}
            with order_lock:
                for txn, data in orders_data.items():
                    result[txn] = ({
                        "transaction_number": txn,
                        "name": data["name"],
                        "type": data["type"],
                        "quantity": data["quantity"]
                    })
            self._send_json_response(200, {"data": result})

        else:
            self._send_json_response(404, {"error": {"code": 404,"message":"Invalid endpoint"}})

    def do_POST(self):
        # if self.path != "/orders":
        #     print("[ORDER_SERVICE] Invalid endpoint")
        #     self._send_json_response(404, {"error": {"code": 404, "message":"Invalid endpoint"}})
        #     return
        global TRANSACTION_ID
        if self.path == "/set_leader":
            content_length = int(self.headers.get('Content-Length', 0))
            print("set leader working", flush=True)
            body = json.loads(self.rfile.read(content_length).decode())
            global LEADER_ID
            LEADER_ID = body.get("leader_id")
            print(f"[INFO] Leader updated to {LEADER_ID}")
            self._send_json_response(200, {"success": True})
            return

        elif self.path == "/propagate":
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode())
            txn_id = body["txn_id"]
            name = body["name"]
            qty = int(body["quantity"])
            trade_type = body["type"]

            with order_lock:
                if txn_id not in orders_data:
                    orders_data[txn_id] = {
                        "name": name,
                        "type": trade_type,
                        "quantity": qty
                    }
                    # global TRANSACTION_ID
                    TRANSACTION_ID = max(TRANSACTION_ID, txn_id)
            self._send_json_response(200, {"success": True})
            return
        
        elif self.path == "/orders":

            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode())
            print(body, flush=True)
            if not self.update_request_input_validation(body):
                return

            name = body["name"]
            qty = int(body["quantity"])
            trade_type = body["type"]

            try:
                if trade_type == "buy":
                    change = -qty
                else:
                    change = qty

                # now, send a request to catalog service to directly update stock
                update_res = requests.post(f"{CATALOG_BASE_URL}/update/{name}/{change}")
                if update_res.status_code != 200:
                    # unsuccessful update, return error response is returned here itself
                    self._send_json_response(update_res.status_code, update_res.json())
                    return

                print("update successful", flush=True)
                # if order is successful, write to in memory storage first
                with order_lock:
                    TRANSACTION_ID += 1
                    orders_data[TRANSACTION_ID] = {
                        "name": name,
                        "type": trade_type,
                        "quantity": qty
                    }

                followers = body.get("followers", [])
                propagation_payload = {
                    "txn_id": TRANSACTION_ID,
                    "name": name,
                    "type": trade_type,
                    "quantity": qty
                }

                for follower_url in followers:
                    try:
                        requests.post(f"{follower_url}/propagate", json=propagation_payload, timeout=2)
                    except Exception as e:
                        print(f"[WARN] Propagation to {follower_url} failed: {e}")

                print("update propagation successful", flush=True)
                #return success response
                self._send_json_response(200, {"data": {"transaction_number": TRANSACTION_ID}})

            except Exception as e:
                print("[!] Error:", e)
                print(traceback.format_exc())
                traceback.print_exc()
                self._send_json_response(500, {"error": {"code": 500, "message":"Internal Server Error"}})
        
        else:
            print("[ORDER_SERVICE] Invalid endpoint")
            self._send_json_response(404, {"error": {"code": 404, "message":"Invalid endpoint"}})
            return
          
def sync_with_peers():

    #wait time for the order service to start
    time.sleep(REPLICA_SYNC_INTERVAL)
    my_id = int(os.environ['ORDER_INSTANCE_ID'])

    # get all the peers from env variables (here we are tryinG to fetch REPLICA_1_URL, REPLICA_2_URL, etc)
    peer_urls = []

    # os.environ gives this particular instance's env variables
    for env_variable in os.environ:
        if (env_variable.startswith("REPLICA_")) and (not env_variable.endswith(str(my_id))) and ("_URL" in env_variable):
            peer_urls.append(os.environ[env_variable])

    # if no peers found, return
    if not peer_urls:
        print("[WARNING][SYNC] No peers found. Exiting sync. [POSSIBLE ERROR]")
        return
    
    global TRANSACTION_ID

    # logic to sync with all peer replicas
    print(f"[SYNC] Trying to sync with: {peer_urls}")
    for peer_url in peer_urls:
        try:
            #get data from each peer
            res = requests.get(f"{peer_url}/sync_missing?from_id={TRANSACTION_ID}")
            if res.status_code == 200:
                data = res.json().get("data", [])

                # rewrite your log with the data from the peer (write only if not already present)
                with order_lock:
                    for row in data:
                        txn = row['transaction_number']
                        if txn not in orders_data:
                            orders_data[txn] = {
                                "name": row["name"],
                                "type": row["type"],
                                "quantity": int(row["quantity"])
                            }
                    TRANSACTION_ID = max(orders_data.keys(), default=0)
                print(f"[SYNC] Synced {len(data)} txns from {peer_url}")
                break
        except Exception as e:
            print(f"[SYNC] Failed to sync from {peer_url}: {e}")

def run():

    # load orders from disk if any
    load_orders_from_disk()

    threading.Thread(target=sync_with_peers, daemon=True).start()

    # start periodic save to disk
    threading.Thread(target=periodic_save_to_disk, daemon=True).start()

    # start server
    server = HTTPServer((ORDER_HOST, ORDER_PORT), OrderHandler)
    executor = ThreadPoolExecutor(max_workers=5)
    print(f"Order Service running on {ORDER_HOST}:{ORDER_PORT}")

    # accept incoming connections
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
