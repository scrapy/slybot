from os.path import join
import json

from slybot.validation.schema import get_schema_validator

def validate_project(specs):
    
    # first stage: validate schemas
    project = specs["project"]
    get_schema_validator("project")(project, project["name"])

    items = specs["items"]
    get_schema_validator("items")(items, "items")

    extractors = specs["extractors"]
    get_schema_validator("extractors")(extractors, "extractors")

    spider_schema_validator = get_schema_validator("spider")
    for spider_name, spider in specs["spiders"].iteritems():
        spider_schema_validator(spider, spider_name)

    return True

