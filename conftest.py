"""Root conftest — ensures both project root and services/api are on sys.path."""
import os
import sys

_root = os.path.dirname(__file__)
_api = os.path.join(_root, "services", "api")

for _p in (_root, _api):
    if _p not in sys.path:
        sys.path.insert(0, _p)
