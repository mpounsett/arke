# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from __future__ import unicode_literals

import hashlib

import arke.domain


def catalogue_hash(domain):
    if isinstance(domain, arke.domain.Domain):
        obj = domain
    else:
        obj = arke.domain.Domain(domain)
    return hashlib.sha1(obj.to_wire()).hexdigest()
