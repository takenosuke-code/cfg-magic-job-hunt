import unittest

from jobbot.links import clean_url


class CleanUrlTest(unittest.TestCase):
    def test_strips_tracking(self):
        url = "https://careers.netapp.com/job/x/27600/1?utm_source=zero2sudo&fbclid=PAZ&id=5"
        self.assertEqual(clean_url(url), "https://careers.netapp.com/job/x/27600/1?id=5")

    def test_keeps_plain_url(self):
        url = "https://jobs.ashbyhq.com/patreon/71f644bc"
        self.assertEqual(clean_url(url), url)


if __name__ == "__main__":
    unittest.main()
