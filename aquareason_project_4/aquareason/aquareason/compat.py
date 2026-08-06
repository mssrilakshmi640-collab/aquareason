"""
Small compatibility fix.

experta depends on frozendict 1.2, which still imports collections.Mapping.
That alias was removed from the collections module in Python 3.10, so on newer
Python versions the import of experta crashes. We map the old names back to
collections.abc before experta is imported. This keeps the project running on
Python 3.8 up to 3.12 without any extra work for the user.
"""
import collections
import collections.abc

for _name in ("Mapping", "MutableMapping", "Sequence", "Iterable", "Callable"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))
