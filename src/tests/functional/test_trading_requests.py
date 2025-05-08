import unittest
import requests

class TestTradeOverbuy(unittest.TestCase):

    def test_overbuy_rejected(self):
        url = "http://frontend_service:8000/orders"
        payload = {
            "name": "GameStart",
            "quantity": 999999,
            "type": "buy"
        }

        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertIn("insufficient", response.json()["error"]["message"].lower())

    def test_invalid_trade_type(self):
        url = "http://frontend_service:8000/orders"
        payload = {
            "name": "GameStart",
            "quantity": 10,
            "type": "invalid_type"
        }

        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertIn("invalid", response.json()["error"]["message"].lower())

    def test_invalid_quantity(self):
        url = "http://frontend_service:8000/orders"
        payload = {
            "name": "GameStart",
            "quantity": -10,
            "type": "buy"
        }
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertIn("invalid", response.json()["error"]["message"].lower())

    def test_invalid_name(self):
        url = "http://frontend_service:8000/orders"
        payload = {
            "name": "INVALIDDD",
            "quantity": 10,
            "type": "buy"
        }
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
        self.assertIn("stock not found", response.json()["error"]["message"].lower())

    def test_invalid_json(self):
        url = "http://frontend_service:8000/orders"
        payload = "invalid_json"
        response = requests.post(url, data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        print("--------")
        print(response.json())
        self.assertIn("invalid", response.json()["error"]["message"].lower())

if __name__ == '__main__':
    unittest.main()
