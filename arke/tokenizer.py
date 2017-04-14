# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from __future__ import unicode_literals

import collections
import enum
import re

from arke.error import UnbalancedParentheses, UnexpectedEOL, UnexpectedEOF

DELIMITERS = [
    ';',
    '(',
    ')',
    '\n',
    '\t',
    ' ',
    '"',
    "'",
]


class TokenType(enum.Enum):
    EOL = 1
    EOF = 2
    SPACE = 3
    COMMENT = 4
    STRING = 5
    WORD = 6


class Token(collections.namedtuple('Token', ['type', 'value', 'position'])):
    pass


class Position(collections.namedtuple('Position', ['line', 'column'])):
    pass


class _Tokenizer(object):
    def __init__(self, f):
        self.f = f

        # set some basic state
        self.multiline = 0
        self.escaped = False
        # "start of line"
        self.SOL = True

    def __iter__(self):
        line = 1
        col = 1

        while True:
            token = None
            tokentype = None

            this_line = line
            this_col = col

            c = self._peek_next()

            if self._is_whitespace(c) and self.SOL and not self.multiline:
                # Whitespace at the start of a line is special, as long as
                # we're not inside a multiline.
                token = self._eat_whitespace()
                tokentype = TokenType.SPACE
                self.SOL = False
                col += token
            elif self._is_whitespace(c):
                col += self._eat_whitespace()
                self.SOL = False
            elif c == '\n':
                if not self.multiline:
                    tokentype = TokenType.EOL
                self.f.read(1)
                self.SOL = True
                line += 1
                col = 1
            elif c == '"':
                # Starting a quoted string
                token = self._get_string()
                tokentype = TokenType.STRING
                col += len(token)
                self.SOL = False
            elif c == ';':
                # Starting a comment
                token = self._get_comment()
                tokentype = TokenType.COMMENT
                self.SOL = False
                col += len(token)
            elif c == '(':
                # starting something multiline
                self.f.read(1)
                self.multiline += 1
                self.SOL = False
                col += 1
            elif c == ')':
                # ending something multiline
                if self.multiline <= 0:
                    raise UnbalancedParentheses
                else:
                    self.f.read(1)
                    self.multiline -= 1
                    self.SOL = False
                    col += 1
            elif c == '':
                # reached the end of the file.  Check what our state is and
                # see if anything is amiss:
                if self.multiline:
                    raise UnexpectedEOF(
                        "EOF while in multiline mode ({})".format(
                            self.multiline)
                    )
                else:
                    tokentype = TokenType.EOF
            else:
                token = self._get_word()
                tokentype = TokenType.WORD
                self.SOL = False
                col += len(token)

            if tokentype:
                yield Token(
                    type=tokentype,
                    value=token,
                    position=Position(this_line, this_col),
                )
                if tokentype == TokenType.EOF:
                    break

    def _peek_next(self):
        x = self.f.tell()
        c = self.f.read(1)
        self.f.seek(x, 0)
        return c

    def _is_whitespace(self, c):
        if re.search(r'\s', c) and c != "\n":
            return True
        else:
            return False

    def _eat_whitespace(self):
        eaten = 0
        while True:
            c = self._peek_next()
            if self._is_whitespace(c):
                self.f.read(1)
                eaten += 1
            else:
                return eaten

    def _get_string(self):
        # The first character should be the opening quote
        value = self.f.read(1)
        while True:
            c = self.f.read(1)
            if c == '\\' and self.escaped is False:
                self.escaped = True
            elif self.escaped is True:
                self.escaped = False
            elif c == '\n':
                raise UnexpectedEOL
            value += c
            if c == '"' and self.escaped is False:
                return value

    def _get_comment(self):
        value = ""
        while True:
            if self._peek_next() == ')' and self.multiline:
                # while in multiline mode, a ) is not part of a comment
                return value
            elif self._peek_next() == "\n":
                self._eat_whitespace()
                return value
            value += self.f.read(1)

    def _get_word(self):
        value = ""
        while True:
            c = self._peek_next()
            if c in DELIMITERS:
                return value
            if c == '':
                self.f.read(1)
                return value
            value += self.f.read(1)
