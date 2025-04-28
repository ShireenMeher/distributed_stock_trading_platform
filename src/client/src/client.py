import http.client
import json
import random
import time
import sys

#for local build
FRONTEND_HOST = 'localhost'  

# for docker buld
# FRONTEND_HOST = 'frontend_service'     

FRONTEND_PORT =  8000             # the port exposed by frontend
BASE_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"

# Adjustable probability p in [0, 1]
p = 0.7

# Sample stock list
stock_names = ["GameStart", "RottenFishCo", "BoarCo", "MenhirCo"]

def client_lookup_request(concurrency, client_id, run_type):

    http_connection = http.client.HTTPConnection(FRONTEND_HOST, FRONTEND_PORT)
    number_of_requests = 10
    all_requests_latencies = 0

    for _ in range(number_of_requests):
        start_time = time.time()
        stock = random.choice(stock_names)
        print(f"\nLooking up: {stock}")

        # Lookup request
        http_connection.request("GET", f"/lookup/{stock}")
        response = http_connection.getresponse()
        data = response.read().decode()
        print(f"[LOOKUP] Response: {response.status}, {data}")

        end_time = time.time()
        single_request_latency = end_time - start_time
        all_requests_latencies += single_request_latency

        time.sleep(1)  # delay between requests

    http_connection.close()
    print("\nSession ended.")
    average_latency = all_requests_latencies / number_of_requests

    # Save the average latency to a log file
    with open(f"logs/lookup_latency_{run_type}_{concurrency}_{client_id}.log", "w") as f:
        f.write(str(average_latency))

        
def client_trade_request(concurrency, client_id, run_type):
    all_requests_latencies = 0
    http_connection = http.client.HTTPConnection(FRONTEND_HOST, FRONTEND_PORT)
    number_of_requests = 10

    for _ in range(number_of_requests):
        start_time = time.time()

        stock = random.choice(stock_names)
        print(f"[TRADE] Placing trade for {stock}")
        type = random.choice(["buy", "sell"])
        quantity = random.randint(1, 10)
        body = json.dumps({"name": stock, "quantity": quantity, "type": type})
        headers = {"Content-Type": "application/json"}
        http_connection.request("POST", "/trade", body=body, headers=headers)
        trade_response = http_connection.getresponse()
        trade_data = trade_response.read().decode()

        if trade_response.status != 200:
            print(f"[WARN] Trade failed for {stock}. Response code: {trade_response.status}")
        else:
            print(f"[TRADE] Response: {trade_response.status}, {trade_data}")
        end_time = time.time()
        single_request_latency = end_time - start_time
        all_requests_latencies += single_request_latency

        # delay between requests
        time.sleep(1)
    average_latency = all_requests_latencies / number_of_requests

    # Save the average latency to a log file
    with open(f"logs/trade_latency_{run_type}_{concurrency}_{client_id}.log", "w") as f:
        f.write(str(average_latency))

    # Close the connection
    http_connection.close()
    print("\nSession ended.")



def client_request_on_probability():
    http_connection = http.client.HTTPConnection(FRONTEND_HOST, FRONTEND_PORT)
    all_requests_latencies = 0
    number_of_requests = 10

    for _ in range(number_of_requests):  # 10 iterations per session
        start_time = time.time()

        stock = random.choice(stock_names)
        print(f"\nLooking up: {stock}")

        # Lookup request
        http_connection.request("GET", f"/stocks/{stock}")
        response = http_connection.getresponse()
        data = response.read().decode()
        print(f"[LOOKUP] Response: {response.status}, {data}")

        try:
            json_data = json.loads(data)
            quantity = int(json_data.get("data", {}).get("quantity", 0))
        except (json.JSONDecodeError, KeyError):
            quantity = 0

        # send trade request based on probability p
        random_number = random.random()
        print(f"[LOOKUP] Random number: {random_number}, Probability p: {p}")
        if quantity > 0 and random_number <= p:
            # Send trade request
            print(f"[TRADE] Placing trade for {stock}")
            type = random.choice(["buy", "sell"])
            quantity = random.randint(1, 10)
            body = json.dumps({"name": stock, "quantity": quantity, "type": type})
            headers = {"Content-Type": "application/json"}
            http_connection.request("POST", "/orders", body=body, headers=headers)
            trade_response = http_connection.getresponse()
            trade_data = trade_response.read().decode()
            print(f"[TRADE] Response: {trade_response.status}, {trade_data}")

        end_time = time.time()
        single_request_latency = end_time - start_time
        all_requests_latencies += single_request_latency

        # delay between requests
        time.sleep(1)  

    http_connection.close()
    print("\nSession ended.")

    average_latency = all_requests_latencies / number_of_requests
    
       

if __name__ == "__main__":
    # lookup or trade request
    request_type = sys.argv[1]  
    concurrency = sys.argv[2]  # number of concurrent clients
    client_id = sys.argv[3]
    run_type = sys.argv[4]  # "docker" or "nondocker"
    
    if request_type == "lookup":
        client_lookup_request(concurrency, client_id, run_type)
    elif request_type == "trade":
        client_trade_request(concurrency, client_id, run_type)