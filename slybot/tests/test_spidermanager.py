from unittest import TestCase
from os.path import dirname, exists, join
from os import walk
import zipfile, tempfile, shutil

from slybot.spidermanager import SlybotSpiderManager, ZipFileSlybotSpiderManager

_PROJECT_DIR = join(dirname(__file__), "data", "Plants")

class _Crawler:
    def __init__(self, settings):
        self.settings = settings

class SpiderManagerTest(TestCase):

    def setUp(self):
        _crawler = _Crawler({"PROJECT_DIR": _PROJECT_DIR})
        self.spidermanager = SlybotSpiderManager.from_crawler(_crawler)

    def test_list(self):
        self.assertEqual(set(self.spidermanager.list()), set(["seedsofchange", "seedsofchange2",
                "seedsofchange.com", "pinterest.com"]))

    def test_create(self):
        spider = self.spidermanager.create("pinterest.com")
        self.assertEqual(spider.name, "pinterest.com")

class ZipFileSpiderManagerTest(TestCase):
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        project_zipfile = join(self.tempdir, "Plants.zip")
        zfile = zipfile.ZipFile(project_zipfile, "w")
        for dname, _, filelist in walk(_PROJECT_DIR):
            for fname in filelist:
                cname = join(dname, fname)
                arcname = cname.replace(_PROJECT_DIR, "")
                zfile.write(cname, arcname)
        zfile.close()
        _crawler = _Crawler({"PROJECT_ZIPFILE": project_zipfile})
        self.spidermanager = ZipFileSlybotSpiderManager.from_crawler(_crawler)

    def test_list(self):
        self.assertEqual(set(self.spidermanager.list()), set(["seedsofchange", "seedsofchange2",
                "seedsofchange.com", "pinterest.com"]))
        self.assertFalse(exists(self.spidermanager.datadir))

    def test_create(self):
        spider = self.spidermanager.create("pinterest.com")
        self.assertEqual(spider.name, "pinterest.com")
        self.assertFalse(exists(self.spidermanager.datadir))

    def test_create_fail(self):
        self.assertRaises(Exception, self.spidermanager.create, "notexists.com")
        self.assertFalse(exists(self.spidermanager.datadir))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

