import unittest
import requests

class TestLookupValid(unittest.TestCase):

    def test_lookup_existing_stock(self):
        stock = "GameStart"
        url = f"http://frontend_service:8000/stocks/{stock}"
        response = requests.get(url)
        print("--------")
        print(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json())
        self.assertEqual(response.json()["data"]["name"], stock)
        self.assertGreaterEqual(response.json()["data"]["quantity"], 0)

    def test_lookup_nonexistent_stock(self):
        url = "http://frontend_service:8000/stocks/UnknownStock"
        response = requests.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
        self.assertIn("stock not found", response.json()["error"]["message"].lower())

    def test_lookup_invalid_url(self):
        url = "http://frontend_service:8000/lookpppp/"
        response = requests.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
        self.assertIn("url not found", response.json()["error"]["message"].lower())

    def test_lookup_invalid_json(self):
        url = "http://frontend_service:8000/stocks/invalid_json"
        response = requests.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
        self.assertIn("stock not found", response.json()["error"]["message"].lower())


if __name__ == '__main__':
    unittest.main()
