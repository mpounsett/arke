# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from more_itertools import peekable

try:
    import threading
    _lock = threading.RLock()
except ImportError:
    _lock = None

DOMAINS = {}


def _acquireLock():
    """Get a lock for serializing access to shared data."""
    if _lock:
        _lock.acquire()


def _releaseLock():
    """Release serialization lock"""
    if _lock:
        _lock.release()


class Domain(object):
    """
    Creates a domain name object, optionally rooted below another ORIGIN
    domain name.  Names that do not specify an ORIGIN are assumed to be fully
    qualified.

    Domain objects should be treated as immutable.  Although they are
    currently implemented as mutable, this is not their intended behaviour and
    will, at some point, be changed.
    """
    def __init__(self, name, origin=None):
        if origin is not None and not isinstance(origin, Domain):
            raise TypeError("origin must be an instance of "
                            "arke.rr.Domain or a subclass")

        if not name.endswith('.') and origin is not None:
            self.origin = origin
        else:
            self.origin = None

        if not self.origin and not name.endswith('.'):
            name += '.'
        self.name = self._label_split(name)

        _acquireLock()
        try:
            if self.fqdn() in DOMAINS:
                self = DOMAINS[self.fqdn()]
            else:
                DOMAINS[self.fqdn()] = self
        finally:
            _releaseLock()

    def __str__(self):
        return self._label_unsplit()

    def __repr__(self):
        return "<{cls}(name='{name}')>".format(
            cls=self.__class__.__name__,
            name=str(self._label_unsplit()),
        )

    def __hash__(self):
        return hash((self.name, self.origin))

    def __eq__(self, other):
        return self.name == other.name and self.origin == other.origin

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return (self.origin > other.origin or
                reversed(self.name) > reversed(other.name))

    def __ge__(self, other):
        return self > other or self == other

    def __lt__(self, other):
        return (self.origin < other.origin or
                reversed(self.name) < reversed(other.name))

    def __le__(self, other):
        return self < other or self == other

    def fqdn(self):
        """
        Return the FQDN of this domain name.  If there is no origin, this is
        the same as the string representation of the object.  If there is an
        origin object, then origins are recursively appended to complete the
        FQDN.
        """
        if not self.origin:
            return str(self)
        return '.'.join((str(self), self.origin.fqdn()))

    def _label_split(self, domain):
        """
        str.split() is insufficient for splitting a domain name into its
        constituent labels because periods inside a label are legal (in text
        representation they must be escaped).

        _label_split() assumes a fully qualified name with the trailing
        period, in order to properly return a set of labels with the null
        (root) label at the end.
        """
        labels = []
        current = []
        i = peekable(iter(domain))
        for c in i:
            if c == '\\':
                if i.peek() == '.':
                    # The next character is an escaped period, so we'll add
                    # it.  We don't add the escape because we want the
                    # individual labels to be stored unescaped
                    current.append(next(i))
                else:
                    try:
                        # the next character is not a period, but is still
                        # escaped for some reason.  Trust that the end
                        # user-knows what they're doing and add the escape and
                        # the following char.
                        current.append(c)
                        current.append(next(i))
                    except StopIteration:
                        pass
            elif c == '.':
                labels.append(''.join(current))
                current = []
            else:
                current.append(c)
        labels.append(''.join(current))
        return tuple(labels)

    def _label_unsplit(self):
        return ".".join(
            map(lambda x: x.replace('.', '\.'), self.name)
        )
