import unittest
from unittest import mock

from jobbot import sources

CSV = b"""Company,Title,URL,Location
NetApp,Software Engineer Intern,https://careers.netapp.com/job/1?utm_source=zero2sudo&fbclid=x,Wichita
,,not a link,
"""


class GoogleSheetTest(unittest.TestCase):
    def test_reads_rows(self):
        with mock.patch.object(sources, "_get", return_value=CSV):
            jobs = sources.google_sheet({"csv_url": "https://example.com/sheet.csv"})
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["company"], "NetApp")
        self.assertEqual(jobs[0]["id"], "sheet:https://careers.netapp.com/job/1")
        self.assertEqual(jobs[0]["locations"], ["Wichita"])

    def test_disabled_without_url(self):
        self.assertEqual(sources.google_sheet({"csv_url": ""}), [])


if __name__ == "__main__":
    unittest.main()
