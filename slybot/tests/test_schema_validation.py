import json
from unittest import TestCase
from os.path import dirname, join

from slybot.validation.schema import get_schema_validator
from slybot.utils import open_project_from_dir

_TEST_PROJECT_DIR = join(dirname(__file__), "data/Plants")

class SchemaValidatorTest(TestCase):

    def test_spec_simple(self):
        obj = {"name": "Slybot Test Project", "version": "1.0"}
        validator = get_schema_validator("project")
        self.assertTrue(validator(obj, "project"))

    def test_spec_simple_required(self):
        obj = {"version": "1.0"}
        validator = get_schema_validator("project")
        self.assertRaisesRegexp(AssertionError, "Required property 'name' not present in object 'project'",
                    validator, obj, "project")

    def test_spec_simple_wrongtype(self):
        obj = {"name": "Slybot Test Project", "version": 1.0}
        validator = get_schema_validator("project")
        self.assertRaisesRegexp(AssertionError, "Wrong type: 'version' must be basestring",
                    validator, obj, "project")

    def test_complex(self):
        """Test complex object"""
        obj = {
            "default": {
                "fields": {
                    "images": {
                        "vary": False, 
                        "required": True, 
                        "type": "image"
                    }, 
                    "url": {
                        "vary": True, 
                        "required": False, 
                        "type": "url"
                    },
                },
            },
            "other": {
                "fields": {
                    "price": {
                        "vary": False, 
                        "required": True, 
                        "type": "price"
                    }, 
                },
            }
        }
        validator = get_schema_validator("items")
        self.assertTrue(validator(obj, "items"))

    def test_complex_required(self):
        obj = {
            "default": {
                "fields": {
                    "images": {
                        "vary": False, 
                        "required": True, 
                    }, 
                    "url": {
                        "vary": True, 
                        "required": False, 
                        "type": "url"
                    },
                },
            },
        }
        validator = get_schema_validator("items")
        self.assertRaisesRegexp(AssertionError, "Required property 'type' not present in object 'images'",
                    validator, obj, "items")
        
    def test_complex_wrongtype(self):
        obj = {
            "default": {
                "fields": {
                    "images": {
                        "vary": False, 
                        "required": True, 
                        "type": False,
                    }, 
                    "url": {
                        "vary": True, 
                        "required": False, 
                        "type": "url"
                    },
                },
            },
        }
        validator = get_schema_validator("items")
        self.assertRaisesRegexp(AssertionError, "Wrong type: 'type' must be basestring, got bool instead",
                    validator, obj, "items")
        
    def test_regex_formatting_wrong(self):
        obj = {
            "0": {
                "regular_expression": "Item: (\d+"
            }
        }
        validator = get_schema_validator("extractors")
        self.assertRaisesRegexp(AssertionError, "Invalid regular expression",
                    validator, obj, "extractors")

    def test_regex_formatting_ok(self):
        obj = {
            "0": {
                "regular_expression": "Item: (\d+)"
            }
        }
        validator = get_schema_validator("extractors")
        self.assertTrue(validator(obj, "extractors"))

    def test_enum_type(self):
        obj = {
            "start_urls": [],
            "links_to_follow": "none",
            "respect_nofollow": True,
            "templates": [],
        }
        validator = get_schema_validator("spider")
        self.assertTrue(validator(obj, "Test spider"))

    def test_enum_type_wrong(self):
        obj = {
            "start_urls": [],
            "links_to_follow": "non",
            "respect_nofollow": True,
            "templates": [],
        }
        validator = get_schema_validator("spider")
        self.assertRaisesRegexp(AssertionError, "Wrong value in enum property", validator, obj, "Test spider")
       
    def test_array_simple(self):
        obj = {
            "start_urls": ['http://www.example.com/'],
            "links_to_follow": "none",
            "respect_nofollow": True,
            "templates": [],
        }
        validator = get_schema_validator("spider")
        self.assertTrue(validator(obj, "Test spider"))

    def test_array_w_format(self):
        obj = {
            "start_urls": ['www.example.com'],
            "links_to_follow": "none",
            "respect_nofollow": True,
            "templates": [],
        }
        validator = get_schema_validator("spider")
        self.assertRaisesRegexp(AssertionError, "Invalid url:", validator, obj, "Test spider")

    def test_objects_array(self):
        obj = {
            "start_urls": ['http://www.example.com'],
            "links_to_follow": "patterns",
            "respect_nofollow": True,
            "templates": [
                {
                    "page_id": "1",
                    "page_type": "item",
                    "scrapes": "default",
                    "url": "http://www.example.com/item1",
                    "extractors": {},
                    "annotated_body": "<html/>",
                    "original_body": "<html/>",
                },
                {
                    "page_id": "2",
                    "page_type": "item",
                    "scrapes": "default",
                    "url": "http://www.example.com/item2",
                    "extractors": {"name": ["e1"], "price": ["e2"]},
                    "annotated_body": "<html/>",
                    "original_body": "<html/>",
                },
            ],
        }
        validator = get_schema_validator("spider")
        self.assertTrue(validator(obj, "Test spider"))

    def test_test_project(self):
        specs = open_project_from_dir(_TEST_PROJECT_DIR)

        project = specs["project"]
        validator = get_schema_validator("project")
        self.assertTrue(validator(project, "My project"))

        items = specs["items"]
        validator = get_schema_validator("items")
        self.assertTrue(validator(items, "my items"))

        extractors = specs["extractors"]
        validator = get_schema_validator("extractors")
        self.assertTrue(validator(extractors, "my extractors"))

        validator = get_schema_validator("spider")
        for name, spider in specs["spiders"].iteritems():
            print name
            self.assertTrue(validator(spider, name))
