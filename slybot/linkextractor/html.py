"""
Link extraction for auto scraping
"""
import re
from urlparse import urljoin
from scrapy.utils.markup import remove_entities
from scrapy.link import Link

from scrapely.htmlpage import HtmlTag, HtmlTagType

from slybot.linkextractor.base import BaseLinkExtractor

_META_REFRESH_CONTENT_RE = re.compile(r"(?P<int>(\d*\.)?\d+)\s*;\s*url=(?P<url>.*)")
_ONCLICK_LINK_RE = re.compile("(?P<sep>('|\"))(?P<url>.+?)(?P=sep)")

class HtmlLinkExtractor(BaseLinkExtractor):
    """Link extraction for auto scraping

    Links (urls and the anchor text) are extracted from HtmlPage objects.

    Some safe normalization is done (always correct, does not make assumptions
    about how the site handles URLs). It allows some customization, which we
    expect to learn for specific websites from the crawl logs.
    """

    def _extract_links(self, htmlpage):
        """Extract links to follow from an html page

        This uses `iterlinks` to read the links in the page.
        """
        return iterlinks(htmlpage)
 
def iterlinks(htmlpage):
    """Iterate through the links in the HtmlPage passed

    For example:
    >>> from scrapely.htmlpage import HtmlPage
    >>> p = HtmlPage(body=u"Please visit <a href='http://scrapinghub.com/'>Scrapinghub</a>")
    >>> iterlinks(p).next()
    Link(url='http://scrapinghub.com/', text=u'Scrapinghub', fragment='', nofollow=False)
    >>> p = HtmlPage(body=u"Go <a href='home.html'>Home</a>")
    >>> iterlinks(p).next()
    Link(url='home.html', text=u'Home', fragment='', nofollow=False)
    
    When a url is specified, absolute urls are made:
    >>> p.url = 'http://scrapinghub.com/'
    >>> iterlinks(p).next()
    Link(url='http://scrapinghub.com/home.html', text=u'Home', fragment='', nofollow=False)

    Base href attributes in the page are respected
    >>> p.body = u"<html><head><base href='myproject/'/></head><body>see my <a href='index.html'>project</a></body>"
    >>> iterlinks(p).next()
    Link(url='http://scrapinghub.com/myproject/index.html', text=u'project', fragment='', nofollow=False)
    >>> p.body = u"<html><head><base href='http://scrape.io/myproject/'/></head><body>see my <a href='index.html'>project</a></body>"
    >>> iterlinks(p).next()
    Link(url='http://scrape.io/myproject/index.html', text=u'project', fragment='', nofollow=False)

    Frameset and iframe urls are extracted
    >>> p = HtmlPage(body=u"<html><frameset><frame src=frame1.html><frame src=frame2.html></frameset><iframe src='iframe.html'/></html>")
    >>> [l.url for l in iterlinks(p)]
    ['frame1.html', 'frame2.html', 'iframe.html']
    
    As are meta refresh tags:
    >>> p = HtmlPage(body=u"<html><head><meta http-equiv='refresh' content='5;url=http://example.com/' />")
    >>> iterlinks(p).next().url
    'http://example.com/'
    
    nofollow is set to True if the link has a rel='nofollow' attribute:
    >>> p = HtmlPage(body=u"<a href='somewhere.html' rel='nofollow'>somewhere</a>")
    >>> list(iterlinks(p))
    [Link(url='somewhere.html', text=u'somewhere', fragment='', nofollow=True)]
    
    It does not require well formed HTML and behaves similar to many browsers
    >>> p = HtmlPage(body=u"<a href='foo'>foo <a href=bar>bar</a><a href='baz'/>baz")
    >>> list(iterlinks(p))
    [Link(url='foo', text=u'foo ', fragment='', nofollow=False), Link(url='bar', text=u'bar', fragment='', nofollow=False), Link(url='baz', text=u'baz', fragment='', nofollow=False)]

    Leading and trailing whitespace should be removed, including in base href
    >>> p = HtmlPage(body=u"<head><base href=' foo/ '/></head><a href='bar '/>baz")
    >>> list(iterlinks(p))
    [Link(url='foo/bar', text=u'baz', fragment='', nofollow=False)]

    Test standard onclick links
    >>> p = HtmlPage(url="http://www.example.com", body=u"<html><td onclick=window.open('page.html?productid=23','win2') >")
    >>> list(iterlinks(p))
    [Link(url='http://www.example.com/page.html?productid=23', text=None, fragment='', nofollow=False)]

    >>> p = HtmlPage("http://www.example.com", body=u"<html><a href='#' onclick=window.open('page.html?productid=24','win2') >")
    >>> list(iterlinks(p))
    [Link(url='http://www.example.com/page.html?productid=24', text=None, fragment='', nofollow=False)]

    >>> p = HtmlPage(body=u"<html><div onclick=window.location.href='http://www.jungleberry.co.uk/Fair-Trade-Earrings/Aguas-Earrings.htm'>")
    >>> list(iterlinks(p))
    [Link(url='http://www.jungleberry.co.uk/Fair-Trade-Earrings/Aguas-Earrings.htm', text=None, fragment='', nofollow=False)]

    Onclick with no href
    >>> p = HtmlPage("http://www.example.com", body=u"<html><a onclick=window.open('page.html?productid=24','win2') >")
    >>> list(iterlinks(p))
    [Link(url='http://www.example.com/page.html?productid=24', text=None, fragment='', nofollow=False)]

    Dont generate link when target is an anchor
    >>> p = HtmlPage("http://www.example.com", body=u"<html><a href='#section1' >")
    >>> list(iterlinks(p))
    []

    Extract links from <link> tags in page header
    >>> p = HtmlPage("http://example.blogspot.com/", body=u"<html><head><link rel='me' href='http://www.blogger.com/profile/987372' /></head><body>This is my body!</body></html>")
    >>> list(iterlinks(p))
    [Link(url='http://www.blogger.com/profile/987372', text=None, fragment='', nofollow=False)]
    """
    base_href = remove_entities(htmlpage.url, encoding=htmlpage.encoding)
    def mklink(url, anchortext=None, nofollow=False):
        url = url.strip()
        fullurl = urljoin(base_href, remove_entities(url, encoding=htmlpage.encoding))
        return Link(fullurl.encode(htmlpage.encoding), text=anchortext, nofollow=nofollow)

    # iter to quickly scan only tags
    tag_iter = (t for t in htmlpage.parsed_body if isinstance(t, HtmlTag))

    # parse body
    astart = ahref = None
    nofollow = False
    for nexttag in tag_iter:
        tagname = nexttag.tag
        attributes = nexttag.attributes
        if tagname == 'a' and (nexttag.tag_type == HtmlTagType.CLOSE_TAG or attributes.get('href') \
                    and not attributes.get('href', '').startswith('#')):
            if astart:
                yield mklink(ahref, htmlpage.body[astart:nexttag.start], nofollow)
                astart = ahref = None
                nofollow = False
            href = attributes.get('href')
            if href:
                ahref = href
                astart = nexttag.end
                nofollow = attributes.get('rel') == u'nofollow'
        elif tagname == 'head':
            # scan ahead until end of head section
            for nexttag in tag_iter:
                tagname = nexttag.tag
                if (tagname == 'head' and \
                        nexttag.tag_type == HtmlTagType.CLOSE_TAG) or \
                        tagname == 'body':
                    break
                if tagname == 'base':
                    href = nexttag.attributes.get('href')
                    if href:
                        joined_base = urljoin(htmlpage.url, href.strip(),
                            htmlpage.encoding)
                        base_href = remove_entities(joined_base, 
                            encoding=htmlpage.encoding)
                elif tagname == 'meta':
                    attrs = nexttag.attributes
                    if attrs.get('http-equiv') == 'refresh':
                        m = _META_REFRESH_CONTENT_RE.search(attrs.get('content', ''))
                        if m:
                            target = m.group('url')
                            if target:
                                yield mklink(target)
                elif tagname == 'link':
                    href = nexttag.attributes.get('href')
                    if href:
                        yield mklink(href)
        elif tagname == 'area':
            href = attributes.get('href')
            if href:
                nofollow = attributes.get('rel') == u'nofollow'
                yield mklink(href, attributes.get('alt', ''), nofollow)
        elif tagname in ('frame', 'iframe'):
            target = attributes.get('src')
            if target:
                yield mklink(target)
        elif 'onclick' in attributes:
            match = _ONCLICK_LINK_RE.search(attributes["onclick"] or "")
            if not match:
                continue
            target = match.group("url")
            nofollow = attributes.get('rel') == u'nofollow'
            yield mklink(target, nofollow=nofollow)

    if astart:
        yield mklink(ahref, htmlpage.body[astart:])


