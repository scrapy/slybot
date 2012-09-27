import os
import json
import zipfile

from zope.interface import implements

from scrapy.interfaces import ISpiderManager
from scrapy.exceptions import NotConfigured

from slybot.spider import IblSpider

class SlybotSpiderManager(object):

    implements(ISpiderManager)

    def __init__(self, datadir=None, project_zipfile=None):
        self.archive = None
        self.datadir = datadir
        self._open = open
        self.listdir = os.listdir
        if project_zipfile is not None:
            self.archive = zipfile.ZipFile(project_zipfile)
            self.datadir = self.archive.namelist()[0].split(os.path.sep)[0]
            self._open = self.archive.open
            self.listdir = lambda x: filter(bool, [os.path.split(f)[-1] for f in self.archive.namelist() if f.startswith(x)])

    @classmethod
    def from_crawler(cls, crawler):
        datadir = crawler.settings.get('PROJECT_DIR')
        if datadir:
            return cls(datadir)
        archive = crawler.settings.get('PROJECT_ZIPFILE')
        if archive:
            return cls(project_zipfile=archive)
        raise NotConfigured

    def create(self, name, **args):
        with self._open(os.path.join(self.datadir, 'spiders', '%s.json' % name)) as f:
            spec = json.load(f)
        with self._open(os.path.join(self.datadir, 'extractors.json')) as f:
            extractors = json.load(f)
        items = self._load_items()
        extractors = dict((e["id"], e) for e in extractors)
        return IblSpider(name, spec, items, extractors, **args)

    def list(self):
        return [i.split(".")[0] for i in self.listdir(os.path.join(self.datadir, "spiders"))]

    def _load_items(self):
        items = {}
        itemsdir = os.path.join(self.datadir, 'items')
        for fname in self.listdir(itemsdir):
            name = fname.split(".")[0]
            with self._open(os.path.join(itemsdir, '%s.json' % name)) as f:
                items[name] = json.load(f)
        return items

