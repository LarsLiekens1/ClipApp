import base64
import os
import unittest
from unittest.mock import patch

import app as clipapp


def basic(password):
    return {"Authorization": "Basic " + base64.b64encode(f"x:{password}".encode()).decode()}


class PasswordTests(unittest.TestCase):
    def setUp(self):
        self.client = clipapp.app.test_client()

    def test_no_password_configured_allows_access(self):
        with patch.dict(os.environ, {"CLIPAPP_PASSWORD": ""}):
            self.assertEqual(self.client.get("/").status_code, 200)

    def test_password_is_required_when_configured(self):
        with patch.dict(os.environ, {"CLIPAPP_PASSWORD": "geheim"}):
            self.assertEqual(self.client.get("/").status_code, 401)
            self.assertEqual(self.client.get("/", headers=basic("fout")).status_code, 401)
            self.assertEqual(self.client.get("/", headers=basic("geheim")).status_code, 200)


if __name__ == "__main__":
    unittest.main()
