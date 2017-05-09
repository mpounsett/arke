# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from __future__ import unicode_literals
from builtins import str, super

from collections import OrderedDict
from enum import Enum
from more_itertools import peekable

import arke.rr

from arke.error import (
    UnexpectedEOL, UnexpectedEOF, UnexpectedToken, MissingData
)
from arke.tokenizer import TokenType


class _ParserStep(Enum):
    oname = 1
    ttl = 2
    rrclass = 3
    rrtype = 4
    rdata = 5
    EOL = 6
    EOF = 7


class _ZoneParser(OrderedDict):
    """
    The zone parser object accepts a generator, which is a stream of
    arke.tokenizer.Token objects, into RRs which it adds to a Zone object.  It
    returns the Zone object.

    'tok' is a generator of arke.tokenizer.Token objects.
    'name' is the name of the zone, and is either a string or an arke.rr.Name
    object.
    'class' is the RRCLASS of the zone, and is either a string or an
    arke.rr.Class object. It defaults to arke.rr.IN.
    """
    def __init__(self, tok, name, cls=arke.rr.IN):
        self.tok = peekable(tok)
        self.zone = Zone(name)
        self.cls = cls

        self.SOL = True
        self.oname = None

        self.reset_state({
            'last_oname': None,
        })
        self.last_step(_ParserStep.EOL)

        self.parse()

    def reset_state(self, start=None):
        # Overwrite current state
        if start is not None:
            self.state = start

        # Reset parser state to the beginning of a line
        self.state.update({
            'next_token': None,
            'oname': None,
            'rrtype': None,
            'rrclass': None,
            'ttl': None,
            'rdata': [],
        })

    def last_step(self, step):
        if step is _ParserStep.EOL:
            self.reset_state()
            self.state['want'] = ['oname', 'comment']
        elif step is _ParserStep.EOF:
            # Nothing to do here, really.
            pass
        elif step is _ParserStep.oname:
            self.state['want'] = ['ttl', 'rrclass', 'rrtype']
        # TTL and RRCLASS can happen in any order, and are both optional. So,
        # for TTL, RRCLASS, and RRTYPE it's necessary to check what we've
        # already obtained, and set the want list appropriately.
        elif step is _ParserStep.ttl:
            self.state['want'] = ['rrclass', 'rrtype']
            for want in ('rrclass', 'rrtype'):
                if self.state[want] is not None:
                    self.state['want'].remove(want)
        elif step is _ParserStep.rrclass:
            self.state['want'] = ['ttl', 'rrtype']
            for want in ('ttl', 'rrtype'):
                if self.state[want] is not None:
                    self.state['want'].remove(want)
        elif step is _ParserStep.rrtype:
            self.state['want'] = ['rdata']
        elif step is _ParserStep.rdata:
            self.state['want'] = ['rdata', 'EOL', 'EOF']

    def qualify(self, name):
        if not name.endswith('.'):
            name = ".".join((name, self.zone.name))
        return name

    def parse(self):
        for tok in self.tok:
            if tok.type is TokenType.COMMENT:
                # Ignoring comments for now.
                pass
            elif tok.type in [TokenType.EOL, TokenType.EOF]:
                if 'EOL' in self.state['want']:
                    rr = self.compile_state()
                    self.reset_state()
                    self.last_step(_ParserStep.EOL)
                    self.zone.add_rr(rr)
                    continue
                else:
                    if tok.type is TokenType.EOL:
                        raise UnexpectedEOL("got unexpected EOL")
                    elif tok.type is TokenType.EOF:
                        raise UnexpectedEOF("got unexpected EOF")
            elif tok.type is TokenType.SPACE:
                # A leading space can be an indication of an RR copying the
                # previous owner name, or an empty line, or a comment.  So,
                # what we do here requires a peek at the next token.
                if self.tok.peek() is TokenType.WORD:
                    # This is leading space before a word... this should be a
                    # new RR using the previous owner name
                    if 'oname' in self.state['want']:
                        self.state['oname'] = self.state['last_oname']
                        self.last_step(_ParserStep.oname)
                # The only other valid next tokens are a comment or EOL (empty
                # line).  Anything else should be an error.  Both cases can be
                # handled fine by the parser when we actually get there, so we
                # won't do anything special here.
            elif tok.type is TokenType.STRING:
                # This was a quoted string.  We better be processing rdata!
                if 'rdata' in self.state['want']:
                    self.state['rdata'].append(tok.value)
                else:
                    raise UnexpectedToken("Unexpected quoted string")
            elif tok.type is TokenType.WORD:
                if 'oname' in self.state['want']:
                    self.state['oname'] = tok.value
                    self.last_step(_ParserStep.oname)
                elif 'rdata' in self.state['want']:
                    self.state['rdata'].append(tok.value)
                    self.last_step(_ParserStep.rdata)
                elif tok.value.isdigit() and 'ttl' in self.state['want']:
                    self.state['ttl'] = int(tok.value)
                    self.last_step(_ParserStep.ttl)
                elif arke.rr.is_type(tok.value):
                    self.state['rrtype'] = arke.rr.get_type_mnemonic(
                        tok.value
                    )
                    self.last_step(_ParserStep.rrtype)
                elif arke.rr.is_class(tok.value):
                    self.state['rrclass'] = arke.rr.get_class_mnemonic(
                        tok.value
                    )
                    self.last_step(_ParserStep.rrclass)
                else:
                    raise UnexpectedToken(
                        "Got unexpected token {!r}".format(tok.type)
                    )

    def compile_state(self):
        # First check that all the required data is present
        for data in ('oname', 'rrtype', 'rdata'):
            if data not in self.state or not self.state[data]:
                raise MissingData(
                    "missing required data ({r}) while compiling RR: {!r}".
                    format(
                        data,
                        map(lambda x, y: "{}: {!r}".format(x, self.state[x]))
                    )
                )
        if self.state['oname'].endswith('.'):
            origin = None
        else:
            origin = arke.domain.Domain(self.zone.name)
        name = arke.domain.Domain(self.state['oname'], origin)
        rrtype = arke.rr.get_type(self.state['rrtype'])
        rrclass = (arke.rr.get_class(self.state['rrclass'])
                   if self.state['rrclass'] else None)
        ttl = self.state['ttl']
        rdata = dict(zip(rrtype._rdata_fields, self.state['rdata']))

        return rrtype(name, rrclass, ttl, self.zone, **rdata)


class Zone(OrderedDict):
    """
    A Zone object is an OrderedDict keyed by arke.domain.Domain objects.
    """
    def __init__(self, name, default_ttl=None):
        super().__init__()

        if not name.endswith('.'):
            name += '.'
        self.name = name

        if default_ttl is not None and type(default_ttl) is not int:
            raise TypeError('default_ttl must be an integer')
        self.default_ttl = default_ttl

    def __str__(self):
        output = []

        if self.default_ttl:
            output.append("$TTL {}".format(self.default_ttl))

        for owner in self.rrs:
            for rr in self.rrs[owner]:
                output.append(str(rr))

        return "\n".join(output) + "\n"

    # TODO: This self.__dict__ comparison doesn't work in 2.7 .. also must
    # implement remaining rich comparison operators.
    def __eq__(self, other):
        if type(self) is type(other):
            if (
                    self.name == other.name and
                    self.__dict__ == other.__dict__
            ):
                return True

    @classmethod
    def from_file(cls, f, name, rrclass=arke.rr.IN):
        parser = _ZoneParser(arke.tokenizer._Tokenizer(f), name, rrclass)
        return parser.parse()

    # TODO: this can likely be made more efficient
    def del_rr(self, **kwargs):
        """
        Delete all resource records matching the attrbitues in **kwargs.
        """
        del_onames = []
        for oname in self.rrs:
            del_rrs = []
            for rr in self.rrs[oname]:
                delete = True
                for k in kwargs:
                    if k not in rr:
                        delete = False
                        break
                    if getattr(rr, k) != kwargs[k]:
                        delete = False
                        break
                if delete:
                    del_rrs.append(rr)
            for rr in del_rrs:
                self.rrs[oname].remove(rr)
            # If an oname has no more RRs then we delete it too
            if len(self.rrs[oname]) == 0:
                del_onames.append(oname)
        for oname in del_onames:
            del(self.rrs[oname])

    def add_rr(self, rr):
        """
        Add a new resource record to the zone.
        """
        oname = rr.oname
        if oname not in self:
            self[oname] = []
        self[oname].append(rr)
