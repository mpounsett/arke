# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------
import os
import sys
import unittest
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                )

import arke.domain


class TestDomainClass(unittest.TestCase):
    def test_name_class(self):
        domain = 'domain\_with.escaped\.characters.in.it.tld.'
        domain_l = ('domain\_with', 'escaped.characters',
                    'in', 'it', 'tld', '')
        domain_r = (
            "<Domain(name='domain\_with.escaped\\.characters.in.it.tld.')>"
        )
        name = arke.domain.Domain(domain)
        self.assertEqual(name.name, domain_l)
        self.assertEqual(str(name), domain)
        self.assertEqual(repr(name), domain_r)

    def test_name_with_origin(self):
        origin = arke.domain.Domain('example.com')
        domain = arke.domain.Domain('www', origin=origin)
        self.assertEqual(domain.fqdn(), 'www.example.com.')
        self.assertEqual(str(domain), 'www')

    @unittest.expectedFailure
    # Need to figure out how to get object equality from the domain generator.
    def test_domain_singleton(self):
        x = arke.domain.Domain('foo.example.com.')
        y = arke.domain.Domain('foo.example.com.')
        print(arke.domain.DOMAINS)
        self.assertEqual(x, y)
        self.assertIs(x, y)
