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
import arke.tokenizer


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
    (arke.tokenizer.TokenType.WORD, '@'),
    (arke.tokenizer.TokenType.WORD, 'IN'),
    (arke.tokenizer.TokenType.WORD, 'SOA'),
    (arke.tokenizer.TokenType.WORD, 'foo.example.com.'),
    (arke.tokenizer.TokenType.WORD, 'hostmaster.example.com.'),
    (arke.tokenizer.TokenType.WORD, '1'),
    (arke.tokenizer.TokenType.COMMENT, 'serial'),
    (arke.tokenizer.TokenType.WORD, '3600'),
    (arke.tokenizer.TokenType.COMMENT, 'refresh'),
    (arke.tokenizer.TokenType.WORD, '3600'),
    (arke.tokenizer.TokenType.COMMENT, 'retry'),
    (arke.tokenizer.TokenType.WORD, '2'),
    (arke.tokenizer.TokenType.COMMENT, 'expiry'),
    (arke.tokenizer.TokenType.WORD, '300'),
    (arke.tokenizer.TokenType.COMMENT, 'negttl '),
    (arke.tokenizer.TokenType.EOL, None),
    (arke.tokenizer.TokenType.SPACE, 4),
    (arke.tokenizer.TokenType.WORD, 'IN'),
    (arke.tokenizer.TokenType.WORD, 'A'),
    (arke.tokenizer.TokenType.WORD, '192.0.2.1'),
    (arke.tokenizer.TokenType.EOL, None),
    (arke.tokenizer.TokenType.WORD, 'foo'),
    (arke.tokenizer.TokenType.WORD, 'IN'),
    (arke.tokenizer.TokenType.WORD, 'A'),
    (arke.tokenizer.TokenType.WORD, '192.0.2.2'),
    (arke.tokenizer.TokenType.EOF, None)
]


class TestTokenizer(unittest.TestCase):
    def test_tokenizer(self):
        t = arke.tokenizer._Tokenizer(StringIO(SAMPLE_TEXT))
        self.assertEqual(list(iter(t)), SAMPLE_TOKEN)
