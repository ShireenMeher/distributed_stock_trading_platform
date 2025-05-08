import http.client
import json
import random
import time
import sys
import datetime

#for local build
FRONTEND_HOST = 'frontend_service'

# for docker buld
# FRONTEND_HOST = 'frontend_service'     

FRONTEND_PORT =  8000             # the port exposed by frontend
BASE_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"

# Adjustable probability p in [0, 1]
# p = 0.7

# Sample stock list
stock_names = ["GameStart", "RottenFishCo", "BoarCo", "MenhirCo", "SwordCo", "ShieldCo", "BowCo", "ArrowCo", "PotionCo", "HelmetCo"]

def client_lookup_request(concurrency, client_id, run_type):

    http_connection = http.client.HTTPConnection(FRONTEND_HOST, FRONTEND_PORT)
    number_of_requests = 10
    all_requests_latencies = 0

    for _ in range(number_of_requests):
        start_time = time.time()
        stock = random.choice(stock_names)
        print(f"\nLooking up: {stock}")

        # Lookup request
        http_connection.request("GET", f"/stocks/{stock}")
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
    number_of_requests = 200

    for _ in range(number_of_requests):
        start_time = time.time()

        stock = random.choice(stock_names)
        print(f"[TRADE] Placing trade for {stock}")
        type = random.choice(["buy", "sell"])
        quantity = random.randint(1, 10)
        body = json.dumps({"name": stock, "quantity": quantity, "type": type})
        headers = {"Content-Type": "application/json"}
        http_connection.request("POST", "/orders", body=body, headers=headers)
        trade_response = http_connection.getresponse()
        trade_data = trade_response.read().decode()

        if trade_response.status != 200:
            print(f"[WARN] Trade failed for {stock}. Response code: {trade_response.status}")
        else:
            print(f"[TRADE] Response: {trade_response.status}, {trade_data}")
            response_json = json.loads(trade_data)
            order_number = response_json.get("data", {}).get("transaction_number")
            if order_number:
                with open("logs/placed_orders.log", "a") as f:
                    f.write(str(order_number) + "\n")
        end_time = time.time()
        single_request_latency = end_time - start_time
        all_requests_latencies += single_request_latency

        # delay between requests
        time.sleep(1)


    # Close the connection
    http_connection.close()
    print("\nSession ended.")

def string_compare_and_match(expected, actual):
    """
    Compare two strings and check if they match.
    """
    expected = expected.lower()
    actual = actual.lower()

    if expected == actual:
        return True
    else:
        return False



def client_request_on_probability(p, client_id):
    placed_orders = []

    http_connection = http.client.HTTPConnection(FRONTEND_HOST, FRONTEND_PORT)
    all_requests_trade_latencies = 0
    all_requests_lookup_latencies = 0
    number_of_requests = 15
    number_of_trades = 0

    for _ in range(number_of_requests):  # 15 iterations per session
        lookup_start_time = time.time()

        stock = random.choice(stock_names)
        print(f"\nLooking up: {stock}")

        # Lookup request
        http_connection.request("GET", f"/stocks/{stock}")
        response = http_connection.getresponse()
        data = response.read().decode()
        print(f"[LOOKUP] Response: {response.status}, {data}")

        lookup_end_time = time.time()
        single_request_lookup_latency = lookup_end_time - lookup_start_time
        all_requests_lookup_latencies += single_request_lookup_latency

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
            number_of_trades += 1
            trade_start_time = time.time()
            print(f"[TRADE] Placing trade for {stock}")
            type = random.choice(["buy", "sell"])
            quantity = random.randint(1, 10)
            body = json.dumps({"name": stock, "quantity": quantity, "type": type})
            headers = {"Content-Type": "application/json"}
            http_connection.request("POST", "/orders", body=body, headers=headers)
            trade_response = http_connection.getresponse()
            trade_data = trade_response.read().decode()
            print(f"[TRADE] Response: {trade_response.status}, {trade_data}")

            trade_end_time = time.time()
            single_request_trade_latency = trade_end_time - trade_start_time
            all_requests_trade_latencies += single_request_trade_latency

            if trade_response.status == 200:
                try:
                    response_json = json.loads(trade_data)
                    order_number = response_json.get("data", {}).get("number")
                    if order_number:
                        placed_orders.append({
                            "order_number": order_number,
                            "order_info": {
                                "name": stock,
                                "quantity": quantity,
                                "type": type
                            }
                        })
                except json.JSONDecodeError:
                    print("[ERROR] Failed to decode trade response JSON")

        # delay between requests
        time.sleep(1)  

    average_lookup_latency = all_requests_lookup_latencies / number_of_requests
    average_trade_latency = all_requests_trade_latencies / number_of_trades if number_of_trades > 0 else 0

    with open(f"logs/cache_lookup_{p}_{client_id}.log", "w") as f:
        f.write(str(average_lookup_latency))
    with open(f"logs/cache_trade_{p}_{client_id}.log", "w") as f:
        f.write(str(average_trade_latency))

    # Now check placed orders
    for order in placed_orders:
        order_number = order["order_number"]
        expected_info = order["order_info"]
        
        # Get order info from server
        http_connection.request("GET", f"/orders/{order_number}")
        order_response = http_connection.getresponse()
        order_data = order_response.read().decode()

        if order_response.status != 200:
            print(f"[ERROR] Failed to retrieve order {order_number}")
            continue

        try:
            order_json = json.loads(order_data)
            server_info = order_json.get("data", {})
            
            name_match = string_compare_and_match(expected_info["name"], server_info.get("name"))
            quantity_match = string_compare_and_match(expected_info["quantity"], server_info.get("quantity"))
            type_match = string_compare_and_match(expected_info["type"], server_info.get("type"))
            
            if name_match and quantity_match and type_match:
                print(f"[OK] Order {order_number} matches")
            else:
                print(f"[MISMATCH] Order {order_number} does not match!")
                print(f"Expected: {expected_info}, Got: {server_info}")
        except json.JSONDecodeError:
            print(f"[ERROR] Failed to decode server response for order {order_number}")

    http_connection.close()
    print("\nSession ended.")


    # ----------------------------------------------------------------------------------------------------
    # now do the same for non cached requests
    # ----------------------------------------------------------------------------------------------------
def client_request_on_probability_without_cache(p, client_id):
    all_requests_trade_latencies = 0
    all_requests_lookup_latencies = 0
    number_of_requests = 15
    number_of_trade_requests = 0
    http_connection = http.client.HTTPConnection(FRONTEND_HOST, FRONTEND_PORT)
    for _ in range(number_of_requests):  # 15 iterations per session
        lookup_start_time = time.time()

        stock = random.choice(stock_names)
        print(f"\nLooking up: {stock}")

        # Lookup request
        http_connection.request("GET", f"/stocks/without/cache/{stock}")
        response = http_connection.getresponse()
        data = response.read().decode()
        print(f"[LOOKUP] Response: {response.status}, {data}")

        # calculate lookup latency
        lookup_end_time = time.time()
        single_request_lookup_latency = lookup_end_time - lookup_start_time
        all_requests_lookup_latencies += single_request_lookup_latency

        try:
            json_data = json.loads(data)
            quantity = int(json_data.get("data", {}).get("quantity", 0))
        except (json.JSONDecodeError, KeyError):
            quantity = 0

        # send trade request based on probability p
        random_number = random.random()
        print(f"[LOOKUP] Random number: {random_number}, Probability p: {p}")
        if quantity > 0 and random_number <= p:
            trade_start_time = time.time()
            number_of_trade_requests += 1
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
            trade_end_time = time.time()
            single_request_trade_latency = trade_end_time - trade_start_time
            all_requests_trade_latencies += single_request_trade_latency

    # calculate average latencies
    average_lookup_latency = all_requests_lookup_latencies / number_of_requests
    average_trade_latency = all_requests_trade_latencies / number_of_trade_requests if number_of_trade_requests > 0 else 0

    # Save the average latencies to log files
    with open(f"logs/nocache_lookup_{p}_{client_id}.log", "w") as f:
        f.write(str(average_lookup_latency))
    with open(f"logs/nocache_trade_{p}_{client_id}.log", "w") as f:
        f.write(str(average_trade_latency))
    
    # Close the connection
    http_connection.close()
    print("\nSession ended.")

if __name__ == "__main__":
    mode = sys.argv[1]  # either 'cached' or 'nocache'
    client_no = (sys.argv[2])
    p = float(sys.argv[3])

    if mode == "cached":
        client_request_on_probability(p, client_no)
    elif mode == "nocache":
        client_request_on_probability_without_cache(p, client_no)
    elif mode == "crash_failure":
        client_trade_request(1, client_no, "crash_failure")
