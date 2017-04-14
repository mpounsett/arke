# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from __future__ import unicode_literals

import os
import sys
import unittest
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                )

import arke.catalogue
import arke.domain


class TestCatalogueMethods(unittest.TestCase):
    def test_hash_from_string(self):
        self.assertEqual(arke.catalogue.catalogue_hash('example.org.'),
                         '47ac1a4d93b61fffdb4762c18c9e7d1a6b046d33')

    def test_hash_from_object(self):
        domain = arke.domain.Domain('example.org.')
        self.assertEqual(arke.catalogue.catalogue_hash(domain),
                         '47ac1a4d93b61fffdb4762c18c9e7d1a6b046d33')
