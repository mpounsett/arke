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

import arke.rr


class TestGetTypeValueMethod(unittest.TestCase):
    def test_from_int(self):
        self.assertEqual(arke.rr.get_type_value(1), 1)

    def test_from_mnemonic(self):
        self.assertEqual(arke.rr.get_type_value('A'), 1)
        self.assertEqual(arke.rr.get_type_value('NS'), 2)
        self.assertEqual(arke.rr.get_type_value('CNAME'), 5)

    def test_from_class(self):
        self.assertEqual(arke.rr.get_type_value(arke.rr.A), 1)
        self.assertEqual(arke.rr.get_type_value(arke.rr.NS), 2)
        self.assertEqual(arke.rr.get_type_value(arke.rr.CNAME), 5)

    def test_from_unknown(self):
        self.assertEqual(arke.rr.get_type_value('TYPE65280'), 65280)


class TestGetTypeMnemonicMethod(unittest.TestCase):
    def test_from_int(self):
        self.assertEqual(arke.rr.get_type_mnemonic(1), 'A')
        self.assertEqual(arke.rr.get_type_mnemonic(65280), 'TYPE65280')

    def test_from_mnemonic(self):
        self.assertEqual(arke.rr.get_type_mnemonic('A'), 'A')
        self.assertEqual(arke.rr.get_type_mnemonic('NS'), 'NS')
        self.assertEqual(arke.rr.get_type_mnemonic('CNAME'), 'CNAME')

    def test_from_class(self):
        self.assertEqual(arke.rr.get_type_mnemonic(arke.rr.A), 'A')
        self.assertEqual(arke.rr.get_type_mnemonic(arke.rr.NS), 'NS')
        self.assertEqual(arke.rr.get_type_mnemonic(arke.rr.CNAME), 'CNAME')

    def test_from_unknown(self):
        self.assertEqual(arke.rr.get_type_mnemonic('TYPE65280'), 'TYPE65280')


class TestGenerateMethods(unittest.TestCase):
    def test_generate_unknown_type(self):
        r = arke.rr._generate_unknown_type(
            65280,
            oname='www.example.com',
            rrclass='IN',
            ttl=200,
            rdata='some random value',
        )
        self.assertIsInstance(r, arke.rr.RR)
        self.assertEqual(r.value, 65280)
        self.assertEqual(r.mnemonic, 'TYPE65280')
        self.assertEqual(r.ttl, 200)
        self.assertEqual(r.rdata, 'some random value')

    def test_generate_from_mnemonic(self):
        r = arke.rr.generate(
            'A',
            oname='www.example.com',
            rrclass='IN',
            ttl=200,
            ip='192.0.2.1',
        )
        self.assertIsInstance(r, arke.rr.A)
        self.assertEqual(r.value, 1)
        self.assertEqual(r.mnemonic, 'A')
        self.assertEqual(r.ttl, 200)
        self.assertEqual(r.ip, '192.0.2.1')

    def test_generate_from_int(self):
        r = arke.rr.generate(
            1,
            oname='www.example.com',
            rrclass='IN',
            ttl=200,
            ip='192.0.2.1',
        )
        self.assertIsInstance(r, arke.rr.A)
        self.assertEqual(r.value, 1)
        self.assertEqual(r.mnemonic, 'A')
        self.assertEqual(r.ttl, 200)
        self.assertEqual(r.ip, '192.0.2.1')

    def test_generate_from_unknown_int(self):
        r = arke.rr.generate(
            65280,
            oname='www.example.com',
            rrclass='IN',
            ttl=200,
            rdata='more random text',
        )
        self.assertIsInstance(r, arke.rr.RR)
        self.assertEqual(r.value, 65280)
        self.assertEqual(r.mnemonic, 'TYPE65280')
        self.assertEqual(r.ttl, 200)
        self.assertEqual(r.rdata, 'more random text')
