try:
    from collections import OrderedDict  # NOQA
except ImportError:  # Python < 2.7
    from ordereddict import OrderedDict  # NOQA

try:
    from urllib.parse import quote, urlencode
except ImportError:  # Python < 3
    from urllib import quote, urlencode


try:
    from collections.abc import MutableMapping
except ImportError:  # Python < 3
    from collections import MutableMapping

try:
    import json
except ImportError:  # Python < 3
    import simplejson as json  # NOQA

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

