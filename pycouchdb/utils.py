# -*- coding: utf-8 -*-

import json
import sys
from collections import OrderedDict

if sys.version_info[0] == 3:
    from urllib.parse import unquote as _unquote
    from urllib.parse import urlunsplit, urlsplit

    string_type = str
    bytes_type = bytes

    from functools import reduce

else:
    from urllib import unquote as _unquote
    from urlparse import urlunsplit, urlsplit

    string_type = unicode
    bytes_type = str

URLSPLITTER = '/'


json_encoder = json.JSONEncoder()


def extract_credentials(url):
    """
    Extract authentication (user name and password) credentials from the
    given URL.

    >>> extract_credentials('http://localhost:5984/_config/')
    ('http://localhost:5984/_config/', None)
    >>> extract_credentials('http://joe:secret@localhost:5984/_config/')
    ('http://localhost:5984/_config/', ('joe', 'secret'))
    >>> extract_credentials('http://joe%40example.com:secret@'
    ...                      'localhost:5984/_config/')
    ('http://localhost:5984/_config/', ('joe@example.com', 'secret'))
    """
    parts = urlsplit(url)
    netloc = parts[1]
    if '@' in netloc:
        creds, netloc = netloc.split('@')
        credentials = tuple(_unquote(i) for i in creds.split(':'))
        parts = list(parts)
        parts[1] = netloc
    else:
        credentials = None
    return urlunsplit(parts), credentials


def _join(head, tail):
    parts = [head.rstrip(URLSPLITTER), tail.lstrip(URLSPLITTER)]
    return URLSPLITTER.join(parts)


def urljoin(base, *path):
    """
    Assemble a uri based on a base, any number of path segments, and query
    string parameters.

    >>> urljoin('http://example.org', '_all_dbs')
    'http://example.org/_all_dbs'

    A trailing slash on the uri base is handled gracefully:

    >>> urljoin('http://example.org/', '_all_dbs')
    'http://example.org/_all_dbs'

    And multiple positional arguments become path parts:

    >>> urljoin('http://example.org/', 'foo', 'bar')
    'http://example.org/foo/bar'

    >>> urljoin('http://example.org/', 'foo/bar')
    'http://example.org/foo/bar'

    >>> urljoin('http://example.org/', 'foo', '/bar/')
    'http://example.org/foo/bar/'

    >>> urljoin('http://example.com', 'org.couchdb.user:username')
    'http://example.com/org.couchdb.user:username'
    """
    return reduce(_join, path, base)


def as_json(response, use_ordered_dict=False):
    if "application/json" in response.headers['content-type']:
        response_src = response.content.decode('utf-8')
        if response.content != b'':
            hook = OrderedDict if use_ordered_dict else None
            return json.loads(response_src, object_pairs_hook=hook)
        else:
            return response_src
    return None


def to_json(doc):
    return json.dumps(doc)


def _path_from_name(name, type):
    """
    Expand a 'design/foo' style name to its full path as a list of
    segments.
    """
    if name.startswith('_'):
        return name.split('/')
    design, name = name.split('/', 1)
    return ['_design', design, type, name]


def encode_view_options(options):
    """
    Encode any items in the options dict that are sent as a JSON string to a
    view/list function.
    """
    retval = {}

    for name, value in options.items():
        if name in ('key', 'startkey', 'endkey'):
            value = json_encoder.encode(value)
        retval[name] = value
    return retval


def force_bytes(data, encoding="utf-8"):
    if isinstance(data, string_type):
        data = data.encode(encoding)
    return data


def force_text(data, encoding="utf-8"):
    if isinstance(data, bytes_type):
        data = data.decode(encoding)
    return data
