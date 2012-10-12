import os
import json

from zope.interface import implements

from scrapy.interfaces import ISpiderManager

from slybot.spider import IblSpider

class SlybotSpiderManager(object):

    implements(ISpiderManager)

    def __init__(self, datadir):
        self.datadir = datadir

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings['PROJECT_DIR'])

    def create(self, name, **args):
        for fname in os.listdir(os.path.join(self.datadir, "spiders")):
            with open(os.path.join(self.datadir, "spiders", fname)) as f:
                spider_spec = json.load(f)
                if spider_spec["name"] == name:
                    break
        else:
            raise KeyError
        with open(os.path.join(self.datadir, 'extractors.json')) as f:
            extractors = json.load(f)
        extractors = dict((e["id"], e) for e in extractors)
        items = self._load_items()
        return IblSpider(name, spider_spec, items, extractors, **args)

    def list(self):
        spiders = []
        for fname in os.listdir(os.path.join(self.datadir, "spiders")):
            with open(os.path.join(self.datadir, "spiders", fname)) as f:
                spec = json.load(f)
                spiders.append(spec["name"])
        return spiders

    def _load_items(self):
        items = {}
        with open(os.path.join(self.datadir, "items.json")) as f:
            itemlist = json.load(f)
            for item in itemlist:
                items[item["id"]] = item
        return items

