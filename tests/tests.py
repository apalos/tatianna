import sys
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class HttpTest(unittest.TestCase):
    #@unittest.skip("demonstrating skipping")
    #def test_skipped(self):
    #    self.fail("shouldn't happen")
    api_obj = None
    open_url = None

    def setUp(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        sys.path.append(os.path.dirname(__file__))
        from core.bot import http_api
        from core.bot import open_url
        self.open_url = open_url
        self.api_obj = http_api()

    def test_wrong_mime(self):
        url = "https://admdownload.adobe.com/bin/live/AdobeReader_dc_en_a_install.dmg"
        self.assertEqual(self.open_url(url)[0], -3)

    def test_wrong_mime_title(self):
        url = "https://admdownload.adobe.com/bin/live/AdobeReader_dc_en_a_install.dmg"
        self.assertEqual(self.api_obj.get_title(url), " ")

    def test_missing_content_length(self):
        url = "http://techcrunch.com/2015/12/03/oculus-announces-rockbandvr/?ncid=rss&cps=gravity_1462_-5971101494545711340"
        self.assertTrue(self.api_obj.get_title(url) != " ")

if __name__ == '__main__':
    import nose
    nose.run(argv=['-vv', '-s'], defaultTest=__name__)

