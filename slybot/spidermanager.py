import os, json
import zipfile
from shutil import rmtree

from zope.interface import implements
from scrapy.interfaces import ISpiderManager
from scrapy.utils.job import job_dir

from slybot.spider import IblSpider

class SlybotSpiderManager(object):

    implements(ISpiderManager)

    def __init__(self, datadir):
        self.datadir = datadir

    @classmethod
    def from_crawler(cls, crawler):
        datadir = crawler.settings['PROJECT_DIR']
        return cls(datadir)

    def create(self, name, **args):
        with open(os.path.join(self.datadir, 'spiders', '%s.json' % name)) as f:
            spec = json.load(f)
        with open(os.path.join(self.datadir, 'extractors.json')) as f:
            extractors = json.load(f)
        items = self._load_items()
        return IblSpider(name, spec, items, extractors, **args)

    def list(self):
        return [os.path.splitext(fname)[0] for fname in \
                    os.listdir(os.path.join(self.datadir, "spiders")) if fname.endswith(".json")]

    def _load_items(self):
        items = {}
        itemsdir = os.path.join(self.datadir, 'items')
        for fname in os.listdir(itemsdir):
            name = fname.split(".")[0]
            with open(os.path.join(itemsdir, '%s.json' % name)) as f:
                items[name] = json.load(f)
        return items

class _AutoCleanZipFile(object):
    def __init__(self, zname, extract_path):
        self.zname = zname
        self.extract_path = extract_path

    def __enter__(self):
        zfile = zipfile.ZipFile(self.zname)
        zfile.extractall(self.extract_path)
        return self

    def __exit__(self, type, value, traceback):
        rmtree(self.extract_path)

class ZipFileSlybotSpiderManager(SlybotSpiderManager):
    
    @classmethod
    def from_crawler(cls, crawler):
        zipname = crawler.settings['PROJECT_ZIPFILE']
        jobdir = job_dir(crawler.settings) or ""
        datadir = os.path.join(jobdir, 'slybot_project_specs')
        return cls(zipname, datadir)

    def __init__(self, zipname, datadir):
        self.zipname = zipname
        super(ZipFileSlybotSpiderManager, self).__init__(datadir)

    def create(self, name, **args):
        with _AutoCleanZipFile(self.zipname, self.datadir) as _:
            return super(ZipFileSlybotSpiderManager, self).create(name, **args)

    def list(self):
        with _AutoCleanZipFile(self.zipname, self.datadir) as _:
            return super(ZipFileSlybotSpiderManager, self).list()
