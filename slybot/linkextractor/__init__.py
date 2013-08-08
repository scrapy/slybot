"""
Link extraction for auto scraping
"""
from scrapy.utils.misc import load_object

from .base import BaseLinkExtractor, ALLOWED_SCHEMES
from .html import HtmlLinkExtractor
from .xml import XmlLinkExtractor, RssLinkExtractor
from .regex import RegexLinkExtractor
from .ecsv import CsvLinkExtractor

_TYPE_MAP = (
    # type, class, ignore value
    ('regex', RegexLinkExtractor, False),
    ('xpath', XmlLinkExtractor, False),
    ('column', CsvLinkExtractor, False),
    ('html', HtmlLinkExtractor, True),
    ('rss', CsvLinkExtractor, True),
)
def create_linkextractor_from_specs(specs):
    """Return a link extractor instance from specs. By default, return a HtmlLinkExtractor.
    """
    specs = specs.copy()
    ltype, value = specs.pop('type'), specs.pop('value')
    if ltype == 'module':
        cls = load_object(value)
        return cls(**specs)
    for key, cls, ignore in _TYPE_MAP:
        if key == ltype:
            if ignore:
                return cls(**specs)
            return cls(value, **specs)
    raise ValueError("Invalid link extractor type specification")
