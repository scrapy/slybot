"""
Images 
"""
from scrapely.extractors import extract_image_url
from slybot.fieldtypes.url import UrlFieldTypeProcessor

class ImagesFieldTypeProcessor(UrlFieldTypeProcessor):
    name = 'image'
    description = 'extracts image URLs'

    def extract(self, text):
        return extract_image_url(text)
        
