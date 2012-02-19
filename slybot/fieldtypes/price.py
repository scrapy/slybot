"""
Price field types
"""
from scrapely import extractors

class PriceTypeProcessor(object):
    """Extracts price from text"""
    name = "price"
    description = "extracts a price decimal number in the text passed"

    def extract(self, htmlregion):
        return extractors.contains_any_numbers(htmlregion.text_content)

    def adapt(self, text, htmlpage):
        return extractors.extract_price(text)

    def render(self, field_name, field_value, item):
        return field_value

