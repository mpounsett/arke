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
            if TYPES[t]._type_value == rrtype:
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
        '_rr_type_value': rrtype,
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
    _type_mnemonic = ""
    _type_value = 0

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
            rrtype=self._type_mnemonic,
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
            cls=self._type_mnemonic,
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


class A(_ADDRESS):
    _type_mnemonic = 'A'
    _type_value = 1
TYPES['A'] = A


class NS(_HOST):
    _type_mnemonic = 'NS'
    _type_value = 2
TYPES['NS'] = NS


class CNAME(_HOST):
    _type_mnemonic = 'CNAME'
    _type_value = 5
TYPES['CNAME'] = CNAME


class SOA(RR):
    _type_mnemonic = 'SOA'
    _type_value = 6
    _rdata_fields = (
        'mname', 'rname', 'serial',
        'refresh', 'retry', 'expiry', 'negttl'
    )
TYPES['SOA'] = SOA


class MB(_HOST):
    _type_mnemonic = 'MB'
    _type_value = 7
TYPES['MB'] = MB


class MG(RR):
    _type_mnemonic = 'MG'
    _type_value = 8
    _rdata_fields = ('mgname',)
TYPES['MG'] = MG


class MR(RR):
    _type_mnemonic = 'MR'
    _type_value = 9
    _rdata_fields = ('newname',)
TYPES['MR'] = MR


class WKS(_ADDRESS):
    _type_mnemonic = 'WKS'
    _type_value = 11
    _rdata_fields = ('ip', 'protocol', 'bitmap')
TYPES['WKS'] = WKS


class PTR(_HOST):
    _type_mnemonic = 'PTR'
    _type_value = 12
TYPES['PTR'] = PTR


class HINFO(RR):
    _type_mnemonic = 'HINFO'
    _type_value = 13
    _rdata_fields = ('cpu', 'os')
TYPES['HINFO'] = HINFO


class MINFO(RR):
    _type_mnemonic = 'MINFO'
    _type_value = 14
    _rdata_fields = ('rmailbox', 'emailbox')
TYPES['MINFO'] = MINFO


class MX(RR):
    _type_mnemonic = 'MX'
    _type_value = 15
    _rdata_fields = ('preference', 'host')
TYPES['MX'] = MX


class TXT(RR):
    _type_mnemonic = 'TXT'
    _type_value = 16
    _rdata_fields = ('txt',)
TYPES['TXT'] = TXT


class RP(RR):
    _type_mnemonic = 'RP'
    _type_value = 17
    _rdata_fields = ('mbox', 'host')
TYPES['RP'] = RP


class AFSDB(MX):
    _type_mnemonic = 'AFSDB'
    _type_value = 18
TYPES['AFSDB'] = AFSDB


class X25(RR):
    _type_mnemonic = 'X25'
    _type_value = 19
    _rdata_fields = ('psdn',)
TYPES['X25'] = X25


class ISDN(RR):
    _type_mnemonic = 'ISDN'
    _type_value = 20
    _rdata_fields = ('pstn', 'sa')
TYPES['ISDN'] = ISDN


class RT(MX):
    _type_mnemonic = 'RT'
    _type_value = 21
TYPES['RT'] = RT


class NSAP(RR):
    _type_mnemonic = 'NSAP'
    _type_value = 22
    _rdata_fields = ('rdata',)
TYPES['NSAP'] = NSAP


class NSAP_PTR(PTR):
    _type_mnemonic = 'NSAP-PTR'
    _type_value = 23
TYPES['NSAP-PTR'] = NSAP_PTR


class PX(RR):
    _type_mnemonic = 'PX'
    _type_value = 26
    _rdata_fields = ('preference', 'map822', 'mapx400')
TYPES['PX'] = PX


class GPOS(RR):
    _type_mnemonic = 'GPOS'
    _type_value = 27
    _rdata_fields = ('longitude', 'latitude', 'altitude')
TYPES['GPOS'] = GPOS


class AAAA(_ADDRESS):
    _type_mnemonic = 'AAAA'
    _type_value = 28
TYPES['AAAA'] = AAAA


class LOC(RR):
    _type_mnemonic = 'LOC'
    _type_value = 29
    _rdata_fields = ('version', 'size', 'hprecision', 'vprecision',
                     'longitude', 'latitude', 'altitude')
TYPES['LOC'] = LOC


class SRV(RR):
    _type_mnemonic = 'SRV'
    _type_value = 33
    _rdata_fields = ('priority', 'weight', 'port', 'target')
TYPES['SRV'] = SRV


class NAPTR(RR):
    _type_mnemonic = 'NAPTR'
    _type_value = 35
    _rdata_fields = ('order', 'preference', 'flags',
                     'services', 'regexp', 'replacement')
TYPES['NAPTR'] = NAPTR


class KX(MX):
    _type_mnemonic = 'KX'
    _type_value = 36
TYPES['KX'] = KX


class CERT(RR):
    _type_mnemonic = 'CERT'
    _type_value = 37
    _rdata_fields = ('type', 'keytag', 'algorithm', 'certificate')
TYPES['CERT'] = CERT


class DNAME(CNAME):
    _type_mnemonic = 'DNAME'
    _type_value = 39
TYPES['DNAME'] = DNAME


class APL(RR):
    _type_mnemonic = 'APL'
    _type_value = 42
    _valid_classes = ('IN',)
    _rdata_fields = ('family', 'prefix', 'n', 'afdlength', 'afdpart')
TYPES['APL'] = APL


class DS(RR):
    _type_mnemonic = 'DS'
    _type_value = 43
    _rdata_fields = ('keytag', 'algorithm', 'dtype', 'digest')
TYPES['DS'] = DS


class SSHFP(RR):
    _type_mnemonic = 'SSHFP'
    _type_value = 44
    _rdata_fields = ('algorithm', 'fptype', 'fingerprint')
TYPES['SSHFP'] = SSHFP


class IPSECKEY(RR):
    _type_mnemonic = 'IPSECKEY'
    _type_value = 45
    _rdata_fields = ('precedence', 'gatewaytype',
                     'algorithm', 'gateway', 'key')
TYPES['IPSECKEY'] = IPSECKEY


# TODO: finish cleaning up templated classes from this point
class RRSIG(RR):
    _type_mnemonic = 'RRSIG'
    _type_value = 46
    _rdata_fields = ('rdata',)
TYPES['RRSIG'] = RRSIG


class NSEC(RR):
    _type_mnemonic = 'NSEC'
    _type_value = 47
    _rdata_fields = ('rdata',)
TYPES['NSEC'] = NSEC


class DNSKEY(RR):
    _type_mnemonic = 'DNSKEY'
    _type_value = 48
    _rdata_fields = ('rdata',)
TYPES['DNSKEY'] = DNSKEY


class DHCID(RR):
    _type_mnemonic = 'DHCID'
    _type_value = 49
    _rdata_fields = ('rdata',)
TYPES['DHCID'] = DHCID


class NSEC3(RR):
    _type_mnemonic = 'NSEC3'
    _type_value = 50
    _rdata_fields = ('rdata',)
TYPES['NSEC3'] = NSEC3


class NSEC3PARAM(RR):
    _type_mnemonic = 'NSEC3PARAM'
    _type_value = 51
    _rdata_fields = ('rdata',)
TYPES['NSEC3PARAM'] = NSEC3PARAM


class TLSA(RR):
    _type_mnemonic = 'TLSA'
    _type_value = 52
    _rdata_fields = ('rdata',)
TYPES['TLSA'] = TLSA


class SMIMEA(RR):
    _type_mnemonic = 'SMIMEA'
    _type_value = 53
    _rdata_fields = ('rdata',)
TYPES['SMIMEA'] = SMIMEA


class Unassigned(RR):
    _type_mnemonic = 'Unassigned'
    _type_value = 54
    _rdata_fields = ('rdata',)
TYPES['Unassigned'] = Unassigned


class HIP(RR):
    _type_mnemonic = 'HIP'
    _type_value = 55
    _rdata_fields = ('rdata',)
TYPES['HIP'] = HIP


class NINFO(RR):
    _type_mnemonic = 'NINFO'
    _type_value = 56
    _rdata_fields = ('rdata',)
TYPES['NINFO'] = NINFO


class RKEY(RR):
    _type_mnemonic = 'RKEY'
    _type_value = 57
    _rdata_fields = ('rdata',)
TYPES['RKEY'] = RKEY


class TALINK(RR):
    _type_mnemonic = 'TALINK'
    _type_value = 58
    _rdata_fields = ('rdata',)
TYPES['TALINK'] = TALINK


class CDS(RR):
    _type_mnemonic = 'CDS'
    _type_value = 59
    _rdata_fields = ('rdata',)
TYPES['CDS'] = CDS


class CDNSKEY(RR):
    _type_mnemonic = 'CDNSKEY'
    _type_value = 60
    _rdata_fields = ('rdata',)
TYPES['CDNSKEY'] = CDNSKEY


class OPENPGPKEY(RR):
    _type_mnemonic = 'OPENPGPKEY'
    _type_value = 61
    _rdata_fields = ('rdata',)
TYPES['OPENPGPKEY'] = OPENPGPKEY


class CSYNC(RR):
    _type_mnemonic = 'CSYNC'
    _type_value = 62
    _rdata_fields = ('rdata',)
TYPES['CSYNC'] = CSYNC


class SPF(RR):
    _type_mnemonic = 'SPF'
    _type_value = 99
    _rdata_fields = ('rdata',)
TYPES['SPF'] = SPF


class UINFO(RR):
    _type_mnemonic = 'UINFO'
    _type_value = 100
    _rdata_fields = ('rdata',)
TYPES['UINFO'] = UINFO


class UID(RR):
    _type_mnemonic = 'UID'
    _type_value = 101
    _rdata_fields = ('rdata',)
TYPES['UID'] = UID


class GID(RR):
    _type_mnemonic = 'GID'
    _type_value = 102
    _rdata_fields = ('rdata',)
TYPES['GID'] = GID


class UNSPEC(RR):
    _type_mnemonic = 'UNSPEC'
    _type_value = 103
    _rdata_fields = ('rdata',)
TYPES['UNSPEC'] = UNSPEC


class NID(RR):
    _type_mnemonic = 'NID'
    _type_value = 104
    _rdata_fields = ('rdata',)
TYPES['NID'] = NID


class L32(RR):
    _type_mnemonic = 'L32'
    _type_value = 105
    _rdata_fields = ('rdata',)
TYPES['L32'] = L32


class L64(RR):
    _type_mnemonic = 'L64'
    _type_value = 106
    _rdata_fields = ('rdata',)
TYPES['L64'] = L64


class LP(RR):
    _type_mnemonic = 'LP'
    _type_value = 107
    _rdata_fields = ('rdata',)
TYPES['LP'] = LP


class EUI48(RR):
    _type_mnemonic = 'EUI48'
    _type_value = 108
    _rdata_fields = ('rdata',)
TYPES['EUI48'] = EUI48


class EUI64(RR):
    _type_mnemonic = 'EUI64'
    _type_value = 109
    _rdata_fields = ('rdata',)
TYPES['EUI64'] = EUI64


class URI(RR):
    _type_mnemonic = 'URI'
    _type_value = 256
    _rdata_fields = ('rdata',)
TYPES['URI'] = URI


class CAA(RR):
    _type_mnemonic = 'CAA'
    _type_value = 257
    _rdata_fields = ('rdata',)
TYPES['CAA'] = CAA


class AVC(RR):
    _type_mnemonic = 'AVC'
    _type_value = 258
    _rdata_fields = ('rdata',)
TYPES['AVC'] = AVC


class TA(RR):
    _type_mnemonic = 'TA'
    _type_value = 32768
    _rdata_fields = ('rdata',)
TYPES['TA'] = TA


class DLV(DS):
    _type_mnemonic = 'DLV'
    _type_value = 32769
TYPES['DLV'] = DLV
