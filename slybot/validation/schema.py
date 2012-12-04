"""Simple validation of specifications passed to slybot"""
from os.path import dirname, join
import json, re
from urlparse import urlparse

_PATH = dirname(__file__)

def load_schemas():
    filename = join(_PATH, "schemas.json")
    return dict((s["$id"], s) for s in json.load(open(filename)))

_SCHEMAS = load_schemas()

def get_schema_validator(schema):
    if isinstance(schema, basestring):
        assert schema in _SCHEMAS, "Error: '%s' is not a valid schema" % schema
        schema = _SCHEMAS[schema]
    stype = schema["type"]
    if stype == "string":
        return StringValidator(schema.get("format"))
    elif stype == "boolean":
        return BooleanValidator()
    elif stype == "array":
        # schema = {"type": schema["items"], "format": schema.get("format")}
        return ArrayValidator(schema["items"])
    elif stype == "object":
        return ObjectValidator(schema)
    elif stype == "mapping":
        # schema = {"type": schema["items"], "format": schema.get("format")}
        return MappingValidator(schema["items"])
    elif stype == "enum":
        return EnumValidator(schema["items"])
    else:
        assert stype in _SCHEMAS, "Error: '%s' is not a valid schema" % stype
        return ObjectValidator(_SCHEMAS[stype])

class NoneValidator(object):
    def __call__(self, value, prop, ptype=type(None)):
        assert isinstance(value, ptype), \
                "Wrong type: '%s' must be %s, got %s instead" % (prop, ptype.__name__, type(value).__name__)
        return True

class StringValidator(NoneValidator):
    def __init__(self, format):
        self.format = format
    def __call__(self, value, prop):
        super(StringValidator, self).__call__(value, prop, basestring)
        if self.format == "regex":
            try:
                re.compile(value)
            except Exception, e:
                raise AssertionError, "Invalid regular expression: %s" % repr(e)
        elif self.format == "url":
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise AssertionError, "Invalid url: '%s'" % value
        return True

class BooleanValidator(NoneValidator):
    def __call__(self, value, prop):
        super(BooleanValidator, self).__call__(value, prop, bool)
        return True

class ArrayValidator(NoneValidator):
    def __init__(self, itemschema):
        self.evalidator = get_schema_validator(itemschema)
    def __call__(self, value, prop):
        super(ArrayValidator, self).__call__(value, prop, list)
        for element in value:
            self.evalidator(element, prop)
        return True

class ObjectValidator(NoneValidator):
    def __init__(self, schema):
        self.schema = schema
    def __call__(self, obj, prop):
        super(ObjectValidator, self).__call__(obj, prop, dict)
        for _prop, schema in self.schema['properties'].items():
            obj_has_prop = _prop in obj.keys()
            if not schema.get("optional", False):
                assert obj_has_prop, "Required property '%s' not present in object '%s'" % (_prop, prop)
            if obj_has_prop:
                value = obj[_prop]
                validator = get_schema_validator(schema)
                validator(value, _prop)
        return True

class MappingValidator(NoneValidator):
    def __init__(self, itemschema):
        self.evalidator = get_schema_validator(itemschema)
    def __call__(self, obj, prop):
        super(MappingValidator, self).__call__(obj, prop, dict)
        for key, value in obj.iteritems():
            self.evalidator(value, key)
        return True

class EnumValidator(NoneValidator):
    def __init__(self, choices):
        self.choices = choices
    def __call__(self, value, prop):
        super(EnumValidator, self).__call__(value, prop, basestring)
        assert value in self.choices, "Wrong value in enum property '%s': '%s'" % (prop, value)
        return True

