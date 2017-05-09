# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from __future__ import unicode_literals

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
import arke.rr

from arke.tokenizer import _Tokenizer
from arke.zone import _ZoneParser, Zone


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


class TestZoneParser(unittest.TestCase):
    def setUp(self):
        self.tok = _Tokenizer(StringIO(SAMPLE_TEXT))
        self.sample_zone = Zone('example.com')
        self.sample_zone.add_rr(
            arke.rr.SOA('example.com', arke.rr.IN, zone=self.sample_zone,
                        mname='foo.example.com.',
                        rname='hostmaster.example.com.',
                        serial=1, refresh=3600, retry=3600, expiry=2,
                        negttl=300)
        )
        self.sample_zone.add_rr(
            arke.rr.A('example.com', arke.rr.IN, zone=self.sample_zone,
                      ip='192.0.2.1')
        )
        self.sample_zone.add_rr(
            arke.rr.A('foo.example.com.', arke.rr.IN, zone=self.sample_zone,
                      ip='192.0.2.2')
        )

    def test_zoneparser(self):
        parser = _ZoneParser(self.tok, 'example.com')
        parser.parse()
        self.assertEqual(self.sample_zone, parser.zone)
