from unittest import TestCase
from os.path import dirname, exists

from slybot.spidermanager import SlybotSpiderManager, ZipFileSlybotSpiderManager

_PATH = dirname(__file__)

class _Crawler:
    def __init__(self, settings):
        self.settings = settings

class SpiderManagerTest(TestCase):

    _crawler = _Crawler({"PROJECT_DIR": "%s/data/Plants" % _PATH})
    spidermanager = SlybotSpiderManager.from_crawler(_crawler)

    def test_list(self):
        self.assertEqual(set(self.spidermanager.list()), set(["seedsofchange", "seedsofchange2",
                "seedsofchange.com", "pinterest.com"]))

    def test_create(self):
        spider = self.spidermanager.create("pinterest.com")
        self.assertEqual(spider.name, "pinterest.com")

class ZipFileSpiderManagerTest(TestCase):
    
    _crawler = _Crawler({"PROJECT_ZIPFILE": "%s/data/Plants.zip" % _PATH, "JOBDIR": "/tmp"})
    spidermanager = ZipFileSlybotSpiderManager.from_crawler(_crawler)

    def test_list(self):
        self.assertEqual(set(self.spidermanager.list()), set(["seedsofchange", "seedsofchange2",
                "seedsofchange.com", "pinterest.com"]))
        self.assertFalse(exists(self.spidermanager.datadir))

    def test_create(self):
        spider = self.spidermanager.create("pinterest.com")
        self.assertEqual(spider.name, "pinterest.com")
        self.assertFalse(exists(self.spidermanager.datadir))

