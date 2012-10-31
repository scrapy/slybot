import json
from unittest import TestCase
from os.path import dirname, join

from scrapy.http import HtmlResponse
from scrapy.utils.reqser import request_to_dict

from scrapely.htmlpage import HtmlPage

from slybot.spidermanager import SlybotSpiderManager

_PATH = dirname(__file__)

class SpiderTest(TestCase):
    smanager = SlybotSpiderManager("%s/data/Plants" % _PATH)

    def test_list(self):
        self.assertEqual(set(self.smanager.list()), set(["seedsofchange", "seedsofchange2",
                "seedsofchange.com", "pinterest.com"]))

    def test_spider_with_link_template(self):
        name = "seedsofchange"
        spider = self.smanager.create(name)
        with open(join(self.smanager.datadir, 'spiders', '%s.json' % name)) as f:
            spec = json.load(f)
        t1, t2 = spec["templates"]
        target1, target2 = [HtmlPage(url=t["url"], body=t["original_body"]) for t in spec["templates"]]

        items, link_regions = spider.extract_items(target1)
        self.assertEqual(items, [])
        self.assertEqual(len(list(spider._process_link_regions(target1, link_regions))), 104)

        items, link_regions = spider.extract_items(target2)
        self.assertEqual(items[0], {
                '_template': u'4fac3b47688f920c7800000f',
                '_type': u'default',
                u'category': [u'Winter Squash'],
                u'days': [None],
                u'description': [u'1-2 lbs. (75-95 days)&nbsp;This early, extremely productive, compact bush variety is ideal for small gardens.&nbsp; Miniature pumpkin-shaped fruits have pale red-orange skin and dry, sweet, dark orange flesh.&nbsp; Great for stuffing, soups and pies.'],
                u'lifecycle': [u'Tender Annual'],
                u'name': [u'Gold Nugget'],
                u'price': [u'3.49'],
                u'product_id': [u'01593'],
                u'species': [u'Cucurbita maxima'],
                'url': u'http://www.seedsofchange.com/garden_center/product_details.aspx?item_no=PS14165',
                u'weight': [None]}
        )
        self.assertEqual(link_regions, [])
        self.assertEqual(len(list(spider._process_link_regions(target2, link_regions))), 0)

    def test_spider_with_link_region_but_not_link_template(self):
        name = "seedsofchange2"
        spider = self.smanager.create(name)
        with open(join(self.smanager.datadir, 'spiders', '%s.json' % name)) as f:
            spec = json.load(f)
        t1, t2 = spec["templates"]

        target1, target2 = [HtmlPage(url=t["url"], body=t["original_body"]) for t in spec["templates"]]
        items, link_regions = spider.extract_items(target1)
        self.assertEqual(items[0], {
                '_template': u'4fad6a7c688f922437000014',
                '_type': u'default',
                u'category': [u'Onions'],
                u'days': [None],
                u'description': [u'(110-120 days)&nbsp; Midsized Italian variety.&nbsp; Long to intermediate day red onion that tolerates cool climates.&nbsp; Excellent keeper.&nbsp; We have grown out thousands of bulbs and re-selected this variety to be the top quality variety that it once was.&nbsp; 4-5&quot; bulbs are top-shaped, uniformly colored, and have tight skins.'],
                u'lifecycle': [u'Heirloom/Rare'],
                u'name': [u'Rossa Di Milano Onion'],
                u'price': [u'3.49'],
                u'species': [u'Alium cepa'],
                u'type': [u'Heirloom/Rare'],
                'url': u'http://www.seedsofchange.com/garden_center/product_details.aspx?item_no=PS15978'}
        )
        self.assertEqual(link_regions, [])

        items, link_regions = spider.extract_items(target2)
        self.assertEqual(items[0], {
                '_template': u'4fad6a7d688f922437000017',
                '_type': u'default',
                u'category': [u'Winter Squash'],
                u'days': [None],
                u'description': [u'1-2 lbs. (75-95 days)&nbsp;This early, extremely productive, compact bush variety is ideal for small gardens.&nbsp; Miniature pumpkin-shaped fruits have pale red-orange skin and dry, sweet, dark orange flesh.&nbsp; Great for stuffing, soups and pies.'],
                u'lifecycle': [u'Tender Annual'],
                u'name': [u'Gold Nugget'],
                u'price': [u'3.49'],
                u'species': [u'Cucurbita maxima'],
                'url': u'http://www.seedsofchange.com/garden_center/product_details.aspx?item_no=PS14165',
                u'weight': [None]}
        )
        self.assertEqual(len(link_regions), 1)
        self.assertEqual(len(list(spider._process_link_regions(target1, link_regions))), 25)
        
    def test_login_requests(self):
        name = "pinterest.com"
        spider = self.smanager.create(name)
        login_request = list(spider.start_requests())[0]
        
        response = HtmlResponse(url="https://pinterest.com/login/", body=open(join(_PATH, "data", "pinterest.html")).read())
        response.request = login_request
        form_request = login_request.callback(response)
        expected = {'_encoding': 'utf-8',
            'body': 'email=test&password=testpass&csrfmiddlewaretoken=nLZy3NMzhTswZvweHJ4KVmq9UjzaZGn3&_ch=ecnwmar2',
            'callback': 'after_login',
            'cookies': {},
            'dont_filter': False,
            'errback': None,
            'headers': {'Content-Type': ['application/x-www-form-urlencoded']},
            'meta': {},
            'method': 'POST',
            'priority': 0,
            'url': u'https://pinterest.com/login/?next=%2F'}

        self.assertEqual(request_to_dict(form_request, spider), expected)
        
        # simulate a simple response to login post from which extract a link
        response = HtmlResponse(url="http://pinterest.com/", body="<html><body><a href='http://pinterest.com/categories'></body></html>")
        result = list(spider.after_login(response))
        self.assertEqual([r.url for r in result], ['http://pinterest.com/categories', 'http://pinterest.com/popular/'])
