import unittest
import requests
import time

FRONTEND_URL='http://frontend_service:8000'
ORDER_REPLICAS = {
    "order_service_1": "http://order_service_1:6001",
    "order_service_2": "http://order_service_2:6002",
    "order_service_3": "http://order_service_3:6003",
}

class TestOrderReplication(unittest.TestCase):

    def test_1_place_order_and_verify(self):
        """Place an order through frontend and verify response"""
        payload = {
            "name": "MenhirCo",
            "type": "buy",
            "quantity": 10,
           
        }
        r = requests.post(f"{FRONTEND_URL}/orders", json=payload)
        self.assertEqual(r.status_code, 200)
        txn_id = r.json()["data"]["transaction_number"]

        # Verify through frontend
        r2 = requests.get(f"{FRONTEND_URL}/orders/{txn_id}")
        self.assertEqual(r2.status_code, 200)
        data = r2.json()["data"]
        self.assertEqual(data["name"], "MenhirCo")
        self.assertEqual(data["quantity"], 10)
        self.assertEqual(data["type"], "buy")

        self.txn_id = txn_id  # store for other tests
        print(f"[PASS] Order placed and verified from frontend: {txn_id}")

    def test_2_replication_to_followers(self):
        """Verify the order is replicated to followers"""
        time.sleep(1)  # wait for propagation
        txn_id = self.get_latest_transaction_id()

        for name, url in ORDER_REPLICAS.items():
            with self.subTest(replica=name):
                r = requests.get(f"{url}/orders/{txn_id}")
                self.assertEqual(r.status_code, 200)
                print(f"[PASS] Replica {name} has txn_id={txn_id}")

    def test_3_manual_crash_and_recovery(self):
        """Manual: Test follower recovers missed txns"""
        print("\n Please stop `order_service_2` container now. Press Enter when done.")
        input()

        payload = {
            "name": "MenhirCo",
            "type": "sell",
            "quantity": 5
        }
        r = requests.post(f"{FRONTEND_URL}/orders", json=payload)
        self.assertEqual(r.status_code, 200)
        txn_id = r.json()["data"]["transaction_number"]

        print("\n Now restart `order_service_2` container. Press Enter after restart.")
        input()

        time.sleep(3)  # wait for sync
        r2 = requests.get(f"{ORDER_REPLICAS['order_service_2']}/orders/{txn_id}")
        self.assertEqual(r2.status_code, 200)
        print(f"[PASS] Recovered follower caught up with txn_id={txn_id}")

    def get_latest_transaction_id(self):
        r = requests.get(f"{FRONTEND_URL}/orders")
        if r.status_code != 200:
            raise Exception("Cannot fetch orders")
        orders = r.json()["data"]
        return max(orders.keys(), default=0)


if __name__ == "__main__":
    unittest.main()
