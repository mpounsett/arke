# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------
import inspect
import os
import sys
import unittest
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                )
from arke.tokenizer import _Tokenizer, TokenType, Position


SAMPLE_TEXT = inspect.cleandoc(
    """
    @ IN SOA foo.example.com. hostmaster.example.com. (
                1 ; serial
                3600; refresh
                3600 ; retry
                2 ; expiry
                300; negttl )
        IN A 192.0.2.1
    foo IN A 192.0.2.2
    """
)

SAMPLE_TOKEN = [
    (TokenType.WORD, '@', Position(line=1, column=1)),
    (TokenType.WORD, 'IN', Position(line=1, column=3)),
    (TokenType.WORD, 'SOA', Position(line=1, column=6)),
    (TokenType.WORD, 'foo.example.com.', Position(line=1, column=10)),
    (TokenType.WORD, 'hostmaster.example.com.', Position(line=1, column=27)),
    (TokenType.WORD, '1', Position(line=2, column=13)),
    (TokenType.COMMENT, '; serial', Position(line=2, column=15)),
    (TokenType.WORD, '3600', Position(line=3, column=13)),
    (TokenType.COMMENT, '; refresh', Position(line=3, column=17)),
    (TokenType.WORD, '3600', Position(line=4, column=13)),
    (TokenType.COMMENT, '; retry', Position(line=4, column=18)),
    (TokenType.WORD, '2', Position(line=5, column=13)),
    (TokenType.COMMENT, '; expiry', Position(line=5, column=15)),
    (TokenType.WORD, '300', Position(line=6, column=13)),
    (TokenType.COMMENT, '; negttl ', Position(line=6, column=16)),
    (TokenType.EOL, None, Position(line=6, column=26)),
    (TokenType.SPACE, 4, Position(line=7, column=1)),
    (TokenType.WORD, 'IN', Position(line=7, column=5)),
    (TokenType.WORD, 'A', Position(line=7, column=8)),
    (TokenType.WORD, '192.0.2.1', Position(line=7, column=10)),
    (TokenType.EOL, None, Position(line=7, column=19)),
    (TokenType.WORD, 'foo', Position(line=8, column=1)),
    (TokenType.WORD, 'IN', Position(line=8, column=5)),
    (TokenType.WORD, 'A', Position(line=8, column=8)),
    (TokenType.WORD, '192.0.2.2', Position(line=8, column=10)),
    (TokenType.EOF, None, Position(line=8, column=19)),
]


class TestTokenizer(unittest.TestCase):
    def test_tokenizer(self):
        t = _Tokenizer(StringIO(SAMPLE_TEXT))
        self.assertEqual(list(iter(t)), SAMPLE_TOKEN)
