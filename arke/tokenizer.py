# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

import enum


class TokenizerError(Exception):
    pass


class UnexpectedEOL(TokenizerError):
    pass


class UnexpectedEOF(TokenizerError):
    pass


class UnbalancedParentheses(TokenizerError):
    pass


class TokenType(enum.Enum):
    EOL = 1
    EOF = 2
    SPACE = 3
    COMMENT = 4
    STRING = 5
    WORD = 6


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


class _Tokenizer(object):
    def __init__(self, f):
        self.f = f

        # set some basic state
        self.multiline = 0
        self.escaped = False
        # "start of line"
        self.SOL = True

    def __iter__(self):
        while True:
            token = None
            tokentype = None

            c = self._peek_next()

            if self._is_whitespace(c) and self.SOL:
                token = self._eat_whitespace()
                tokentype = TokenType.SPACE
                self.SOL = False
            elif self._is_whitespace(c):
                self._eat_whitespace()
                self.SOL = False
            elif c == '\n' and not self.multiline:
                self.f.read(1)
                tokentype = TokenType.EOL
                self.SOL = True
            elif c == '"':
                # Starting a quoted string
                token = self._get_string()
                tokentype = TokenType.STRING
                self.SOL = False
            elif c == ';':
                # Starting a comment
                token = self._get_comment()
                tokentype = TokenType.COMMENT
                self.SOL = False
            elif c == '(':
                # starting something multiline
                self.f.read(1)
                self.multiline += 1
                self.SOL = False
            elif c == ')':
                # ending something multiline
                if self.multiline <= 0:
                    raise UnbalancedParentheses
                else:
                    self.f.read(1)
                    self.multiline -= 1
                    self.SOL = False
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

            if tokentype:
                yield (tokentype, token)
                if tokentype == TokenType.EOF:
                    break

    def _peek_next(self):
        x = self.f.tell()
        c = self.f.read(1)
        self.f.seek(x, 0)
        return c

    def _is_whitespace(self, c):
        if self.multiline and c == '\n':
            return True
        elif c == '\n':
            return False
        elif c.isspace():
            return True

    def _eat_whitespace(self):
        eaten = 0
        while 1:
            c = self._peek_next()
            if self._is_whitespace(c):
                self.f.read(1)
                eaten += 1
            else:
                return eaten

    def _get_string(self):
        value = ""
        # eat the opening quote char
        c = self.f.read(1)
        while 1:
            if self._peek_next() == '"' and self.escaped is False:
                # eat the closing quote
                self.f.read(1)
                return value
            c = self.f.read(1)
            if c == '\\' and self.escaped is False:
                self.escaped = True
            elif self.escaped is True:
                self.escaped = False
            elif c == '\n':
                raise UnexpectedEOL
            value += c

    def _get_comment(self):
        value = ""
        # eat the opening semicolon and whitespace
        self.f.read(1)
        self._eat_whitespace()
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
        while 1:
            c = self._peek_next()
            if c in DELIMITERS:
                return value
            if c == '':
                self.f.read(1)
                return value
            value += self.f.read(1)


class _MasterParser(object):
    def __init__(self):
        pass
