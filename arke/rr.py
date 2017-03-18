# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

import re

TYPES = {}

CLASSES = {
    1: ['IN', 'Internet'],
    3: ['CH', 'Chaos'],
    4: ['HS', 'Hesiod'],
    255: ['ANY', 'ANY'],
}


def generate(rrtype, **kwargs):
    """
    Return the requested subclass of the RR object.

    This method is generally only meant to be used for unknown RR types,
    or RR types not yet implemented by this library.  For RR types implemented
    by this library it's better to directly instantiate that RR type's class.

    'rrtype' can be a valid class, an integer, a known type mnemonic, or
    TYPE### unknown type notation from RFC3597

    'kwargs' varies by RR type, however for unknown types this can only be a
    hash with the single key 'rdata' and the opaque data to be included in the
    record.
    """
    if issubclass(rrtype, RR):
        return rrtype(**kwargs)
    elif isinstance(rrtype, int):
        for t in TYPES:
            if TYPES[t].value == rrtype:
                return TYPES[t](**kwargs)
        else:
            return _generate_unknown_type(rrtype, **kwargs)
    elif isinstance(rrtype, str):
        if rrtype.upper() in TYPES:
            return TYPES[rrtype.upper()](**kwargs)
        else:
            match = re.search(r'^TYPE(\d+)$', rrtype)
            if match:
                return generate(match.group(1), **kwargs)
    raise ValueError(
        "rrtype must be a known type mnemonic (e.g. A, MX), an integer, "
        "or a TYPE#### text representation of an unknown type (see RFC3597)"
    )


def _generate_unknown_type(rrtype, **kwargs):
    assert isinstance(rrtype, int), "rrtype must be an int"
    classname = 'TYPE{}'.format(rrtype)
    classvars = {
        'value': rrtype,
        'mnemonic': classname,
    }
    newclass = type(classname, (RR,), classvars)
    TYPES[newclass] = rrtype
    TYPES[rrtype] = newclass
    return newclass(**kwargs)


def _get_class_value(rrclass):
    if type(rrclass) is int:
        return rrclass
    if type(rrclass) is str:
        match = re.search(r'^CLASS(\d+)$', rrclass)
        if match:
            return int(match.group(1))
        for k in CLASSES:
            if rrclass in CLASSES[k]:
                return k
    raise ValueError(
        "rrclass must be a known class mnemonic (e.g. IN, CH), an integer, "
        "or a CLASS### text representation of an unknown class (see RFC3597)"
    )


def _get_class_mnemonic(rrclass):
    if rrclass in CLASSES:
        return CLASSES[rrclass][0]
    if type(rrclass) is int:
        return "CLASS{}".format(rrclass)
    if type(rrclass) is str:
        match = re.search(r'^CLASS(\d+)$', rrclass)
        if match:
            return rrclass
        for k in CLASSES:
            if rrclass in CLASSES[k]:
                return rrclass
    raise ValueError(
        "rrclass must be a known class mnemonic (e.g. IN, CH), an integer, "
        "or a CLASS### text representation of an unknown class (see RFC3597)"
    )


def _get_class_long_name(rrclass):
    if type(rrclass) is str:
        return _get_class_long_name(_get_class_value(rrclass))
    if type(rrclass) is int:
        if rrclass in CLASSES:
            return CLASSES[rrclass][1]
        return "CLASS{}".format(rrclass)
    raise ValueError(
        "rrclass must be a known class mnemonic (e.g. IN, CH), an integer, "
        "or a CLASS### text representation of an unknown class (see RFC3597)"
    )


class RR(object):
    """
    Resource Record (RR) base class

    Subclass this to implement individual record types.
    """

    # Override this value in subclasses with the mnemonic and integer type
    # code from the IANA Resource Record Types registry
    mnemonic = ""
    value = 0

    # A list of class mnemonics valid for this RR type.  A value of ('*',)
    # indicates this RR can be used in any class.
    _valid_classes = ('*',)

    # A list of the RDATA fields for this RR type
    _rdata_fields = ()

    # The default format string for this RR ttype's string representation.
    # This can be overridden to add formatting (e.g. field widths).  If
    # self.zone is set to a valid Zone object, and that object has a
    # _global_fmt_str parameter, that format string will be used in
    # place of this.
    _fmt_str = "{oname} {ttl} {rrclass} {rrtype} {rdata}"

    def __init__(self, oname, rrclass, ttl=None, zone=None, **rdata):
        """
        Initialize a new RR object.

        Valid rdata keys are defined by _rdata_fields.  Any invalid keys are
        silently ignored.
        """
        if (self._valid_classes[0] != '*' and
                _get_class_mnemonic(rrclass) not in self._valid_classes):
            raise (
                ValueError,
                "rrclass {!r} not valid for this RR type".format(rrclass)
            )
        self.oname = oname
        self.rrclass = _get_class_value(rrclass)
        self.ttl = ttl
        self.zone = zone

        for field in self._rdata_fields:
            if field in rdata:
                try:
                    setattr(self, field, rdata[field])
                    del(rdata[field])
                except KeyError:
                    raise (KeyError,
                           "rdata field {!r} is required".format(field))

    def __str__(self):
        if self.zone and hasattr(self.zone, '_global_fmt_str'):
            fmt = self.zone._global_fmt_str
        else:
            fmt = self._fmt_str

        return fmt.format(
            oname=self.oname,
            ttl=self.ttl if self.ttl is not None else "",
            rrclass=_get_class_mnemonic(self.rrclass),
            rrtype=self.mnemonic,
            rdata=" ".join(map(
                lambda x: getattr(self, x),
                self._rdata_fields
            )),
        )

    def __repr__(self):
        fmt = (
            "<{cls}(oname={oname!r},rrclass={rrclass!r},ttl={ttl!r},{rdata})>"
        )
        return fmt.format(
            cls=self.mnemonic,
            oname=self.oname,
            rrclass=_get_class_mnemonic(self.rrclass),
            ttl=self.ttl,
            rdata=",".join(
                map(
                    lambda x: "{}={!r}".format(x, getattr(self, x)),
                    self._rdata_fields
                )
            )
        )


class _ADDRESS(RR):
    """Parent class for RRs with an address as the first (or only) field in
    its RDATA"""
    _rdata_fields = ('ip',)


class _HOST(RR):
    """Parent class for RRs with a host name as the first (or only) field in
    its RDATA"""
    _rdata_fields = ('host',)


# Type classes are based on RFC definitions for each RR type.  The best
# starting place for specifics is the IANA DNS Parameters registry.  RR types
# are listed at
# https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml#dns-parameters-4

# Excluded from the below types are any types that:
# 1) are marked as obsolete
# 2) do not have a specification listed
# 3) meta-types (e.g. ANY) and other types seen only on the wire
# 4) are marked as experimental
# 5) are defined outside the RFC series
#
# (1) should not be implemented as they are obsolete.  (2) cannot be
# implemented since there is no specification.
# (3) will be implemented later, when this library is in need of wire-only
# types
# Excluding (4) and (5) is purely a work-saving measure, and isn't due to any
# prejudice against those record types.  They should be added if any users of
# this library need them, or when someone sufficiently pedantic comes along
# and contributes code.

class A(_ADDRESS):
    mnemonic = 'A'
    value = 1
TYPES['A'] = A


class NS(_HOST):
    mnemonic = 'NS'
    value = 2
TYPES['NS'] = NS


class CNAME(_HOST):
    mnemonic = 'CNAME'
    value = 5
TYPES['CNAME'] = CNAME


class SOA(RR):
    mnemonic = 'SOA'
    value = 6
    _rdata_fields = (
        'mname', 'rname', 'serial',
        'refresh', 'retry', 'expiry', 'negttl'
    )
TYPES['SOA'] = SOA


class MB(_HOST):
    mnemonic = 'MB'
    value = 7
TYPES['MB'] = MB


class MG(RR):
    mnemonic = 'MG'
    value = 8
    _rdata_fields = ('mgname',)
TYPES['MG'] = MG


class MR(RR):
    mnemonic = 'MR'
    value = 9
    _rdata_fields = ('newname',)
TYPES['MR'] = MR


class WKS(_ADDRESS):
    mnemonic = 'WKS'
    value = 11
    _rdata_fields = ('ip', 'protocol', 'bitmap')
TYPES['WKS'] = WKS


class PTR(_HOST):
    mnemonic = 'PTR'
    value = 12
TYPES['PTR'] = PTR


class HINFO(RR):
    mnemonic = 'HINFO'
    value = 13
    _rdata_fields = ('cpu', 'os')
TYPES['HINFO'] = HINFO


class MINFO(RR):
    mnemonic = 'MINFO'
    value = 14
    _rdata_fields = ('rmailbox', 'emailbox')
TYPES['MINFO'] = MINFO


class MX(RR):
    mnemonic = 'MX'
    value = 15
    _rdata_fields = ('preference', 'host')
TYPES['MX'] = MX


class TXT(RR):
    mnemonic = 'TXT'
    value = 16
    _rdata_fields = ('txt',)
TYPES['TXT'] = TXT


class RP(RR):
    mnemonic = 'RP'
    value = 17
    _rdata_fields = ('mbox', 'host')
TYPES['RP'] = RP


class AFSDB(MX):
    mnemonic = 'AFSDB'
    value = 18
TYPES['AFSDB'] = AFSDB


class X25(RR):
    mnemonic = 'X25'
    value = 19
    _rdata_fields = ('psdn',)
TYPES['X25'] = X25


class ISDN(RR):
    mnemonic = 'ISDN'
    value = 20
    _rdata_fields = ('pstn', 'sa')
TYPES['ISDN'] = ISDN


class RT(MX):
    mnemonic = 'RT'
    value = 21
TYPES['RT'] = RT


class NSAP(RR):
    mnemonic = 'NSAP'
    value = 22
    _rdata_fields = ('rdata',)
TYPES['NSAP'] = NSAP


class NSAP_PTR(PTR):
    mnemonic = 'NSAP-PTR'
    value = 23
TYPES['NSAP-PTR'] = NSAP_PTR


class PX(RR):
    mnemonic = 'PX'
    value = 26
    _rdata_fields = ('preference', 'map822', 'mapx400')
TYPES['PX'] = PX


class GPOS(RR):
    mnemonic = 'GPOS'
    value = 27
    _rdata_fields = ('longitude', 'latitude', 'altitude')
TYPES['GPOS'] = GPOS


class AAAA(_ADDRESS):
    mnemonic = 'AAAA'
    value = 28
TYPES['AAAA'] = AAAA


class LOC(RR):
    mnemonic = 'LOC'
    value = 29
    _rdata_fields = ('version', 'size', 'hprecision', 'vprecision',
                     'longitude', 'latitude', 'altitude')
TYPES['LOC'] = LOC


class SRV(RR):
    mnemonic = 'SRV'
    value = 33
    _rdata_fields = ('priority', 'weight', 'port', 'target')
TYPES['SRV'] = SRV


class NAPTR(RR):
    mnemonic = 'NAPTR'
    value = 35
    _rdata_fields = ('order', 'preference', 'flags',
                     'services', 'regexp', 'replacement')
TYPES['NAPTR'] = NAPTR


class KX(MX):
    mnemonic = 'KX'
    value = 36
TYPES['KX'] = KX


class CERT(RR):
    mnemonic = 'CERT'
    value = 37
    _rdata_fields = ('type', 'keytag', 'algorithm', 'certificate')
TYPES['CERT'] = CERT


class DNAME(CNAME):
    mnemonic = 'DNAME'
    value = 39
TYPES['DNAME'] = DNAME


class APL(RR):
    mnemonic = 'APL'
    value = 42
    _valid_classes = ('IN',)
    _rdata_fields = ('family', 'prefix', 'n', 'afdlength', 'afdpart')
TYPES['APL'] = APL


class DS(RR):
    mnemonic = 'DS'
    value = 43
    _rdata_fields = ('keytag', 'algorithm', 'dtype', 'digest')
TYPES['DS'] = DS


class SSHFP(RR):
    mnemonic = 'SSHFP'
    value = 44
    _rdata_fields = ('algorithm', 'fptype', 'fingerprint')
TYPES['SSHFP'] = SSHFP


class IPSECKEY(RR):
    mnemonic = 'IPSECKEY'
    value = 45
    _rdata_fields = ('precedence', 'gatewaytype',
                     'algorithm', 'gateway', 'key')
TYPES['IPSECKEY'] = IPSECKEY


class RRSIG(RR):
    mnemonic = 'RRSIG'
    value = 46
    _rdata_fields = ('covered', 'algorithm', 'labels', 'origttl', 'expire',
                     'inception', 'keytag', 'signer', 'signature')
TYPES['RRSIG'] = RRSIG


class NSEC(RR):
    mnemonic = 'NSEC'
    value = 47
    _rdata_fields = ('next', 'typemap')
TYPES['NSEC'] = NSEC


class DNSKEY(RR):
    mnemonic = 'DNSKEY'
    value = 48
    _rdata_fields = ('flags', 'protocol', 'algorithm', 'key')
TYPES['DNSKEY'] = DNSKEY


class DHCID(RR):
    mnemonic = 'DHCID'
    value = 49
    _rdata_fields = ('rdata',)
TYPES['DHCID'] = DHCID


class NSEC3(RR):
    mnemonic = 'NSEC3'
    value = 50
    _rdata_fields = ('algorithm', 'flags', 'optout',
                     'iterations', 'salt', 'next', 'typemap')
TYPES['NSEC3'] = NSEC3


class NSEC3PARAM(RR):
    mnemonic = 'NSEC3PARAM'
    value = 51
    _rdata_fields = ('algorithm', 'flags', 'iterations', 'salt')
TYPES['NSEC3PARAM'] = NSEC3PARAM


class TLSA(RR):
    mnemonic = 'TLSA'
    value = 52
    _rdata_fields = ('usage', 'selector', 'matching', 'association')
TYPES['TLSA'] = TLSA


class SMIMEA(TLSA):
    mnemonic = 'SMIMEA'
    value = 53
TYPES['SMIMEA'] = SMIMEA


class HIP(RR):
    mnemonic = 'HIP'
    value = 55
    _rdata_fields = ('algorithm', 'hit', 'pubkey', 'serverlist')
TYPES['HIP'] = HIP


class CDS(DS):
    mnemonic = 'CDS'
    value = 59
    _rdata_fields = ('rdata',)
TYPES['CDS'] = CDS


class CDNSKEY(DNSKEY):
    mnemonic = 'CDNSKEY'
    value = 60
    _rdata_fields = ('rdata',)
TYPES['CDNSKEY'] = CDNSKEY


class OPENPGPKEY(RR):
    mnemonic = 'OPENPGPKEY'
    value = 61
    _rdata_fields = ('key',)
TYPES['OPENPGPKEY'] = OPENPGPKEY


class CSYNC(RR):
    mnemonic = 'CSYNC'
    value = 62
    _rdata_fields = ('soa', 'flags', 'typemap')
TYPES['CSYNC'] = CSYNC


class SPF(TXT):
    mnemonic = 'SPF'
    value = 99
TYPES['SPF'] = SPF


class NID(RR):
    mnemonic = 'NID'
    value = 104
    _rdata_fields = ('preference', 'node')
TYPES['NID'] = NID


class L32(RR):
    mnemonic = 'L32'
    value = 105
    _rdata_fields = ('preference', 'ip')
TYPES['L32'] = L32


class L64(RR):
    mnemonic = 'L64'
    value = 106
    _rdata_fields = ('preference', 'locator')
TYPES['L64'] = L64


class LP(MX):
    mnemonic = 'LP'
    value = 107
TYPES['LP'] = LP


class EUI48(RR):
    mnemonic = 'EUI48'
    value = 108
    _rdata_fields = ('address',)
TYPES['EUI48'] = EUI48


class EUI64(RR):
    mnemonic = 'EUI64'
    value = 109
    _rdata_fields = ('address',)
TYPES['EUI64'] = EUI64


class URI(RR):
    mnemonic = 'URI'
    value = 256
    _rdata_fields = ('priority', 'weight', 'target')
TYPES['URI'] = URI


class CAA(RR):
    mnemonic = 'CAA'
    value = 257
    _rdata_fields = ('flags', 'tag', 'value')
TYPES['CAA'] = CAA


class DLV(DS):
    mnemonic = 'DLV'
    value = 32769
TYPES['DLV'] = DLV
