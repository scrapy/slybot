==============
Slybot crawler
==============

Slybot is a Python web crawler for doing web scraping. It's implemented on top of the
`Scrapy`_ web crawling framework and the `Scrapely`_ extraction library.

Requirements
============

* `Scrapy`_
* `Scrapely`_


Usage
=====

In order to run `Scrapy`_ with the slybot spider, you need just to have slybot library in your python path,
and pass the appropiate settings. In ``slybot/settings.py`` you can find a sample settings file, which
for being complete needs only to be given a value to ``PROJECT_DIR`` or ``PROJECT_ZIPFILE`` settings::

    SPIDER_MANAGER_CLASS = 'slybot.spidermanager.SlybotSpiderManager'
    EXTENSIONS = {'slybot.closespider.SlybotCloseSpider': 1}
    ITEM_PIPELINES = ['slybot.dupefilter.DupeFilterPipeline']
    SLYDUPEFILTER_ENABLED = True
    # PROJECT_DIR = 
    # PROJECT_ZIPFILE =

    try:
        from local_slybot_settings import *
    except ImportError:
        pass

The first line::

    SPIDER_MANAGER_CLASS = 'slybot.spidermanager.SlybotSpiderManager'

is where the magic starts. It says to scrapy to use the slybot spider manager, which is required in order to load and
run the slybot spider.

The line::
    
    EXTENSIONS = {'slybot.closespider.SlybotCloseSpider': 1}
    
is optional, but recommended. As slybot spiders are not absolutely customizable as a common scrapy spider, it
can face some unexpected and uncontrollable situations thad leads them to a neverending crawling. The
specified extension is a safe measure in order to avoid that. It works by checking each fixed period of time, that
a minimal number of items has been scraped along the same period. Refer to ``slybot/closespider.py`` for details

The also optional ``DupeFilterPipeline``, which is enabled with the lines::

    ITEM_PIPELINES = ['slybot.dupefilter.DupeFilterPipeline']
    SLYDUPEFILTER_ENABLED = True

filters out duplicate items based on the item version, which is calculated using the version
fields of the item definition (defined below). It maintains a set of the version of each item issued by the spider,
and if the version of a new item is already in the set, it is dropped.

The settings ``PROJECT_DIR`` and ``PROJECT_ZIPFILE`` defines where the slybot spider can find the project
specifications (item definitions, extractors, spiders). It is a string that defines the path either of a folder
or a zipfile in your filesystem, with a folder structure that we will define below in this doc.

So, if you know how to use scrapy, you already know the alternatives to pass those settings to the crawler: just use your
customized settings module with all the settings you need, or use the slybot.settings module and give the remaining
settings in a ``local_slybot_settings.py`` file somewhere in your python path, or pass the additional settings in command
line. You can right now do a test with our test project in ``slybot/tests/data/`` inside your slybot local repository::
    
    SCRAPY_PROJECT_ZIPFILE=<slybot local repo>/slybot/tests/data/Plants.zip SCRAPY_SETTINGS_MODULE=slybot.settings scrapy list

or::

    SCRAPY_PROJECT_DIR=<slybot local repo>/slybot/tests/data/Plants SCRAPY_SETTINGS_MODULE=slybot.settings scrapy list

and then use the scrapy ``crawl`` command for run one of the spiders that gives the list

Project specification folder structure
======================================

If you list the contents of ``slybot/tests/data/Plants`` or ``slybot/tests/data/Plants.zip`` you will find
the same structure::

            Plants/items/default.json
            Plants/spiders/seedsofchange.json
            Plants/spiders/seedsofchange2.json
            Plants/extractors.json

There is a base folder, ``Plants/`` with the name of the project, then a subfolder ``item`` which contains one json
file for the specification of each item classes used by the spiders, a subfolder ``spiders`` with json format specifications
of each spider in the project, and a file extractors.json which defines the extractors used by spiders (which are usually
common to many of them)

Below we will explain the schema properties for each specification.

How the spider works, in short
==============================

The slybot spider uses the instance based learning extractor algorithm of `Scrapely`_ library, which is feeded by spider templates,
a set of html pages with some extra html tags that marks from where data must be extracted. Basically, the extractor
algorithm tries to match template marks (annotations) onto target pages in order to extract data from them.

Each template specification (defined inside spiders specification) associates the template to a required item specification
and to an optional series of custom extractors specifications, both of which in turn defines rules that helps the extraction
algorithm to work properly.

The item field type property defines, among other things, the base extractor that will be applied over the raw html code extracted
by the application of template. For example, the ``raw`` type makes no change at all over the extracted data. The ``text`` type
removes every html markup content and leaves only the text content of the extracted data. The ``number`` type extracts only the
number part (if any) of the extracted data. And so on.

You can modify and tune the default behaviour for a given template, using custom extractors, either by replacing the default base (type)
extractor with a different one, or appending a regular expression extractor which will refine the result of the base extractor.

Item class specification schema
===============================

As we saw, inside the folder ``<project name>/items/`` there is a json file for each item class that are referred in templates. The
item json object is a key-value map with two fields:

id
  A string that identifies the item, which its value is the same as the json file name (without the .json extension).

properties
  A definition of the properties of the item fields. A list.

In turn, each element of the properties list is a key-value map with the properties specifications. Each properties specification
map consists of the following key-value pairs:

name
  The name of the field

description
  The description of the item field. It is an arbitrary string, including empty one.

required
  A boolean (can take the json values true or false). This field is used in the extractor algorithm in order to determine whether
  the extracted data using a particular template is valid. If some of the required fields is not present in the
  extracted data, then all the data is considered invalid and it is ignored.

type
  The type of the item field. A string with fixed range of values. Must be the name of one of the supported field type processors. In
  order to get the list of valid names, you can write the following lines in a python console::

    >>> from slybot.fieldtypes import FieldTypeManager
    >>> FieldTypeManager._FULLMAP.keys()
  
vary
  Either true or false. This field is used by the duplicates pipeline described above in order to build the item version.
  Only item fields with vary value ``false`` in its properties will be considered for calculating the item version. Thus, an
  item field specified with a vary value ``true`` means that the same item can appear more than once in the site, with a different
  value in the given field. The most typical example is a field that contains the URL from which the data was extracted from.
  Usually the same data can be extracted from two or more different URLs. If the item field that stores this value were defined
  as vary ``false``, then the extracted data in different URLs would have a different item version value, and thus be considered
  as different items by the duplicates pipeline.

Spider specification schema
===========================

Inside folder ``<project_name>/spiders/`` there is one json formatted file for the specifications of each spider. Each file
contains a json object which defines a key-value map with the following properties:

name
  A string that identifies the spider (the same as the json file with the spider specs, without the .json extension)

start_urls
  A list of the urls that the spider with start the crawling from.

links_to_follow
  The follow links mode. At moment it can take one of two string values: "patterns" and "none". If "none", it will not follow links,
  so the only pages that will be visited are the start urls. If "pattern", it will follow links according to regular expression
  patterns given in ``follow_patterns`` property.

follow_patterns
  A list containing url patterns (python regular expressions) that the found link urls has to match in order to be followed by the
  spider. If empty (and ``follow`` value is "patterns"), will follow any link.

exclude_patterns
  A list containing url patterns (python regular expressions) that must not be followed by the spider (has precedence over 
  ``follow_patterns``)

respect_nofollow
  Some links in a web page comes with a tag rel='nofollow', a directive meant for bots in order not to follow them. The slybot spider
  will respect this directive, unless respect_nofollow be given the value false.

templates
  A list of templates specifications (see next section)

Templates specification schema
==============================

Each template specification is a json object with the following properties:

page_id
  A string that identifies the template. Can have any format, so it can be system specific, but should be unique at least among
  templates of the same spider if you want to identify uniquely the template used in the extraction of a particular item.

page_type
  Currently it can take one of two different values, "item" and "links". "links" type template are intended only for the purpose
  of extracting links from any page where it is applied, and annotations on this kind of template are a means to restrict the are
  from which to extract links. While "item" type templates are intended for extraction of items, and its annotations indicates where
  in a page to extract item data from. You can also annotate link areas in an item template, so you can also restrict the areas from
  which to extract links in this kind of page.

scrapes
  The id of the item class that template extracts.

extractors
  A list of extractors ids, each one matching to one of the extractors of the project (see `How the spider works, in short`_ and
  `Extractors specification schema`_)

url
  The URL of the original page from which the template was generated from.

original_body
  The html source of the original page (the one from which the template was generated from)

annotated_body
  The html source of the annotated template

Extractors specification schema
===============================

When you specify the type of an item class, one of the things you are defining is a type extractor, which will be applied to
the raw html extracted data.

The file ``<project name>/extractors.json`` contains a list of json objects which will define the extractor specifications,
defined by the following properties:

id
  The id of the extractor

field_name
  The name of the field that the extractor will be applied to (must match one of the fields defined in the item class used by
  the template).

type_extractor
  If present, it will replace the default base extractor, as explained in `How the spider works, in short`_. Must be the same
  range of valid type identifiers than item field ``type`` property.

regular_expression
  If present, the given regular expression will generate an extractor that will be appended to the type one (either the default
  defined in the item, or the type extractor that replaced it), and refine its result (see again, `How the spider works, in short`_).
  The given regular expression must have at least one regular expression group (parenthesis enclosed part), in order to be valid.
  The groups matches will be concatenated for generating the final result.

In the list of extractors of a template, you can specify at most one type extractor per field (which, as said, will replace the
default one of the item class for the given field, and so will always be the first extractor to be applied over the raw result), and
any amount of regular expression extractors you may want, the input of each one being the output of the previous one. The regular
expression extractors for the same field will be applied in order of appearance in the list of extractors for the given template.

The reason to define extractors separately from the list of extractors of a template, is that usually the same extractor patterns
are shared among many templates of the same spider.

Specification Schemas fast reference
====================================

As mentioned above, you can find an example of a complete project specification in the ``slybot/tests/data`` folder, either as
unzipped and zipped versions. Let's quick define all the schemas that were described in detail above, in an easy human readable
way. For purpose of programatic validation (coming soon), json schemas specifications is provided in ``slybot/validation/project.json``
folder.

Item class schema::

    {'id': string,
     'properties': [field 1 properties, field 2 properties, ...]
    }

Field property schema::

    {'name': string,
     'description': string,
     'required': boolean,
     'type': a field type identifier,
     'vary': boolean
    }

Spider specification schema::

    {'name': string,
     'start_urls': [url 1, url 2, ...],
     'links_to_follow': either 'pattern' or 'none',
     'follow_patterns': [follow pattern 1, follow pattern 2, ...],
     'exclude_patterns': [exclude pattern 1, exclude pattern 2, ...],
     'respect_nofollow': boolean,
     'templates': [template 1 specs, template 2 specs, ...]
    }

Template specification schema::

    {'page_id': string,
     'page_type: either 'item' or 'links',
     'scrapes': an item class id,
     'extractors': [extractor 1 id, extractor 2 id, ...],
     'url': an url,
     'original_body': an html source,
     'annotated_body' an html source
    }

Extractors specification schema::

    {'id': string,
     'field_name': a field name,
     'type extractor': a field type identifier,
     'regular_expression': a regular expression pattern
    }

.. _Scrapy: https://github.com/scrapy/scrapy
.. _Scrapely: https://github.com/scrapy/scrapely

