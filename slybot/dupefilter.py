"""
Duplicates filter middleware for autoscraping
"""
from scrapy.exceptions import NotConfigured
from scrapy.exceptions import DropItem

from slybot.item import create_item_version

class DupeFilterPipeline(object):
    def __init__(self, settings):
        if not settings.getbool('SLYDUPEFILTER_ENABLED'):
            raise NotConfigured
        self._itemversion_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_item(self, item, spider):
        """Checks whether a scrapy item is a dupe, based on version (not vary)
        fields of the item class"""
        item_cls = spider.itemcls_info[item['_type']]['class']

        if not item_cls.version_fields:
            return item
        version = create_item_version(item_cls, item)
        if version in self._itemversion_cache:
            old_url = self._itemversion_cache[version]
            raise DropItem("Duplicate product scraped at <%s>, first one was scraped at <%s>" % (item["url"], old_url))
        self._itemversion_cache[version] = item["url"]
        return item

