import re
import unittest

import app as clipapp


class PageTests(unittest.TestCase):
    def setUp(self):
        self.client = clipapp.app.test_client()

    def test_pages_and_their_static_files_load(self):
        for page in ("/", "/editor"):
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200, page)
            html = response.get_data(as_text=True)
            response.close()
            assets = re.findall(r'(?:src|href)="(/static/[^"]+)"', html)
            self.assertTrue(assets, page)
            for asset in assets:
                r = self.client.get(asset)
                self.assertEqual(r.status_code, 200, asset)
                r.close()


if __name__ == "__main__":
    unittest.main()
