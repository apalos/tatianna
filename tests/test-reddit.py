import sys
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class RedditTest(unittest.TestCase):
    #@unittest.skip("demonstrating skipping")
    #def test_skipped(self):
    #    self.fail("shouldn't happen")
    api_obj = None
    open_url = None
    reddit_obj = None

    def setUp(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        sys.path.append(os.path.dirname(__file__))
        from core.bot import reddit_feed
        from core.bot import open_url
        self.open_url = open_url
        self.reddit_obj = reddit_feed()

    def test_reddit_feed(self):
        res = self.reddit_obj.get_reddit_url()
        print res


if __name__ == '__main__':
    import nose
    nose.run(argv=['-vv', '-s'], defaultTest=__name__)

