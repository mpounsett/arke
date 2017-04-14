# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from __future__ import unicode_literals


class ArkeError(Exception):
    pass


class TokenizerError(ArkeError):
    pass


class UnexpectedEOL(TokenizerError):
    pass


class UnexpectedEOF(TokenizerError):
    pass


class UnbalancedParentheses(TokenizerError):
    pass


class ParserError(ArkeError):
    pass


class UnexpectedToken(ParserError):
    pass


class MissingData(ParserError):
    pass
