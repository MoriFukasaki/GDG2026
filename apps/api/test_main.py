import unittest

from fastapi.testclient import TestClient

from main import app
from public_hello import app as public_app


class ApiSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_hello_returns_plain_text(self) -> None:
        response = self.client.get("/api/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "hello world")
        self.assertTrue(response.headers["content-type"].startswith("text/plain"))

    def test_web_is_served(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("PDF", response.text)

    def test_public_app_exposes_only_hello(self) -> None:
        client = TestClient(public_app)
        self.assertEqual(client.get("/api/hello").text, "hello world")
        self.assertEqual(client.get("/api/health").status_code, 404)
        self.assertEqual(client.post("/api/questions").status_code, 404)


if __name__ == "__main__":
    unittest.main()
