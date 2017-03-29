# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Copyright 2017, Matthew Pounsett <matt@conundrum.com>
# ------------------------------------------------------------

from more_itertools import peekable

import re

TYPES = {}

CLASSES = {}


def generate(rrtype, **kwargs):
    """
    Return an instance of the requested subclass of the RR class.

    'rrtype' can be a valid class, an integer, a known type mnemonic, or
    TYPE### unknown type notation from RFC3597

    'kwargs' varies by RR type, however for unknown types this can only be a
    hash with the single key 'rdata' and the opaque data to be included in the
    record.

    While this method can be used to generate an instance of any RR type's
    class, it is of particular use for generating unknown types based on the
    type's int value.
    """
    rrtype = get_type_mnemonic(rrtype)
    if rrtype in TYPES:
        rrtype = TYPES[rrtype]
    else:
        rrtype = _generate_unknown_type(get_type_value(rrtype))
    return rrtype(**kwargs)


class Name(object):
    def __init__(self, name):
        self.name = self._label_split(name)

    def __str__(self):
        return self._label_unsplit()

    def __repr__(self):
        return "<{cls}(name='{name}')>".format(
            cls=self.__class__.__name__,
            name=str(self._label_unsplit()),
        )

    def _label_split(self, domain):
        """
        str.split() is insufficient for splitting a domain name into its
        constituent labels because periods inside a label are legal (in text
        representation they must be escaped).

        _label_split() assumes a fully qualified name with the trailing
        period, in order to properly return a set of labels with the null
        (root) label at the end.
        """
        labels = []
        current = []
        i = peekable(iter(domain))
        for c in i:
            if c == '\\':
                if i.peek() == '.':
                    # The next character is an escaped period, so we'll add
                    # it.  We don't add the escape because we want the
                    # individual labels to be stored unescaped
                    current.append(next(i))
                else:
                    try:
                        # the next character is not a period, but is still
                        # escaped for some reason.  Trust that the end
                        # user-knows what they're doing and add the escape and
                        # the following char.
                        current.append(c)
                        current.append(next(i))
                    except StopIteration:
                        pass
            elif c == '.':
                labels.append(''.join(current))
                current = []
            else:
                current.append(c)
        labels.append(''.join(current))
        return labels

    def _label_unsplit(self):
        return ".".join(
            map(lambda x: x.replace('.', '\.'), self.name)
        )


def is_class(rrclass):
    for k in CLASSES:
        if rrclass.upper() in CLASSES[k]:
            return True
    if re.search(r'^CLASS\d+$', rrclass.uppper()):
        return True
    else:
        return False


def get_class(rrclass):
    if type(rrclass) is type and issubclass(rrclass, Class):
        return rrclass
    else:
        return _generate_unknown_class(get_class_value(rrclass))


def get_class_value(rrclass):
    """
    Accept an RR class identifier and return the appropriate integer class
    value.

    rrclass may be one of:
    - a known class mnemonic (e.g. IN)
    - an integer corresponding to a known or unknown RR class (returns itself)
    - a CLASS### text representation of a known or unknown class (see RFC3597)
    """
    if type(rrclass) is type and issubclass(rrclass, Class):
        return rrclass.value
    elif isinstance(rrclass, int):
        return rrclass
    elif isinstance(rrclass, str):
        if rrclass.upper() in CLASSES:
            return CLASSES[rrclass.upper()].value
        else:
            match = re.search(r'^CLASS(\d+)$', rrclass)
            if match:
                return int(match.group(1))
    raise ValueError(
        "rrclass must be a known class mnemonic (e.g. IN, CH), an integer, "
        "or a CLASS### text representation of an unknown class (see RFC3597) "
        "({!r} is a {})".format(rrclass, type(rrclass))
    )


def get_class_mnemonic(rrclass):
    """
    Accept an RR class identifier and return the appropriate text class
    mnemonic.

    rrclass may be one of:
    - a known class mnemonic (e.g. IN) (returns itself)
    - an integer corresponding to a known or unknown RR class
    - a CLASS### text representation of a known or unknown class (see RFC3597)
    """
    if type(rrclass) is type and issubclass(rrclass, Class):
        return rrclass.mnemonic
    elif isinstance(rrclass, int):
        for cls in CLASSES:
            if rrclass == CLASSES[cls].value:
                return CLASSES[cls].mnemonic
        return "CLASS{}".format(int(rrclass))
    elif isinstance(rrclass, str):
        if rrclass.upper() in CLASSES:
            return CLASSES[rrclass.upper()].mnemonic
        else:
            match = re.search(r'^CLASS(\d+)$', rrclass.upper())
            if match:
                return rrclass
    raise ValueError(
        "rrclass must be a known class mnemonic (e.g. IN, CH), an integer, "
        "or a CLASS### text representation of an unknown class (see RFC3597) "
        "({!r} is a {})".format(rrclass, type(rrclass))
    )


def get_class_name(rrclass):
    """
    Accept an RR class identifier and return the appropriate text long name
    for the class.

    rrclass may be one of:
    - a known class mnemonic (e.g. IN)
    - an integer corresponding to a known or unknown RR class
    - a CLASS### text representation of a known or unknown class (see RFC3597)
    """
    if type(rrclass) is type and issubclass(rrclass, Class):
        return rrclass.long_name
    elif isinstance(rrclass, int):
        for cls in CLASSES:
            if rrclass == CLASSES[cls].value:
                return CLASSES[cls].long_name
    elif isinstance(rrclass, str):
        if rrclass.upper() in CLASSES:
            return CLASSES[rrclass.upper()].long_name
        else:
            match = re.search(r'^CLASS(\d+)$', rrclass.upper())
            if match:
                return rrclass
    raise ValueError(
        "rrclass must be a known class mnemonic (e.g. IN, CH), an integer, "
        "or a CLASS### text representation of an unknown class (see RFC3597) "
        "({!r} is a {})".format(rrclass, type(rrclass))
    )


def _generate_unknown_class(rrclass):
    assert isinstance(rrclass, int), "rrclass must be an int"
    mnemonic = get_class_mnemonic(rrclass)
    class_attributes = {
        'value': rrclass,
        'mnemonic': mnemonic,
        'long_name': mnemonic,
    }
    newclass = type(str(mnemonic), (Class,), class_attributes)
    CLASSES[mnemonic] = newclass
    return newclass


class Class(object):
    """
    RR Class base class

    Subclass this to implement individual RR classes.
    """
    mnemonic = None
    long_name = None
    value = 0


class IN(Class):
    mnemonic = 'IN'
    long_name = 'Internet'
    value = 1
CLASSES['IN'] = IN


class CH(Class):
    mnemonic = 'CH'
    long_name = 'Chaos'
    value = 3
CLASSES['CH'] = CH


class HS(Class):
    mnemonic = 'HS'
    long_name = 'Hesiod'
    value = 4
CLASSES['HS'] = HS


def is_type(rrtype):
    if isinstance(rrtype, RR):
        return True
    elif type(rrtype) is type and issubclass(rrtype, RR):
        return True
    elif rrtype.upper() in TYPES:
        return True
    elif re.search(r'^TYPE\d+$', rrtype.upper()):
        return True
    else:
        return False


def get_type_value(rrtype):
    """
    Accept an RR type identifier and return the appropriate integer type
    value.

    rrtype may be one of:
    - a known type mnemonic (e.g. A, MX)
    - an integer corresponding to a known or unknown RR type (returns itself)
    - a TYPE#### text representation of a known or unknown type (see RFC3597)
    """
    if type(rrtype) is type and issubclass(rrtype, RR):
        return rrtype.value
    elif isinstance(rrtype, int):
        return rrtype
    elif isinstance(rrtype, str):
        if rrtype.upper() in TYPES:
            return TYPES[rrtype.upper()].value
        else:
            match = re.search(r'^TYPE(\d+)$', rrtype)
            if match:
                return int(match.group(1))
    raise ValueError(
        "rrtype must be a known type mnemonic (e.g. A, MX), an integer, "
        "or a TYPE#### text representation of an unknown type (see RFC3597) "
        "({!r} is a {})".format(rrtype, type(rrtype))
    )


def get_type_mnemonic(rrtype):
    """
    Accept a RR type identifier and return the appropriate mnemonic.

    rrtype may be one of:
    - a known type mnemonic (e.g. A, MX) (returns itself)
    - an integer corresponding to a known or unknown RR type
    - a TYPE#### text representation of a known or unknown type (see RFC3597)
    """
    if type(rrtype) is type and issubclass(rrtype, RR):
        return rrtype.mnemonic
    elif isinstance(rrtype, int):
        for t in TYPES:
            if TYPES[t].value == rrtype:
                return t
        return "TYPE{}".format(rrtype)
    elif isinstance(rrtype, str):
        if rrtype.upper() in TYPES:
            return rrtype.upper()
        else:
            match = re.search(r'^TYPE(\d+)$', rrtype)
            if match:
                return rrtype
    raise ValueError(
        "rrtype must be a known type mnemonic (e.g. A, MX), an integer, "
        "or a TYPE#### text representation of an unknown type (see RFC3597) "
        "({!r} is a {})".format(rrtype, type(rrtype))
    )


def _generate_unknown_type(rrtype):
    assert isinstance(rrtype, int), "rrtype must be an int"
    mnemonic = 'TYPE{}'.format(rrtype)
    type_attributes = {
        'value': rrtype,
        'mnemonic': mnemonic,
    }
    newclass = type(str(mnemonic), (RR,), type_attributes)
    TYPES[mnemonic] = newclass
    return newclass


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
    _rdata_fields = ('rdata',)

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
                get_class_mnemonic(rrclass) not in self._valid_classes):
            raise (
                ValueError,
                "rrclass {!r} not valid for this RR type".format(rrclass)
            )
        self.oname = oname
        self.rrclass = get_class(rrclass)
        self.ttl = ttl
        self.zone = zone

        for field in self._rdata_fields:
            try:
                setattr(self, field, rdata[field])
                del(rdata[field])
            except KeyError:
                raise KeyError("rdata field {!r} is required".format(field))

    def __str__(self):
        if self.zone and hasattr(self.zone, '_global_fmt_str'):
            fmt = self.zone._global_fmt_str
        else:
            fmt = self._fmt_str

        return fmt.format(
            oname=self.oname,
            ttl=self.ttl if self.ttl is not None else "",
            rrclass=get_class_mnemonic(self.rrclass),
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
            rrclass=get_class_mnemonic(self.rrclass),
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
