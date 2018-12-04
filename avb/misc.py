from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils
from .core import AVBProperty
from . import mobid

from . utils import (
    read_byte,
    read_s8,
    read_bool,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_u64le,
    read_string,
    read_doublele,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    read_raw_uuid,
    iter_ext,
    read_assert_tag,
    peek_data
)

@utils.register_class
class FileLocator(core.AVBObject):
    class_id = b'FILE'
    properties = [
        AVBProperty('path_name', 'OMFI:FL:PathName', 'string'),
        AVBProperty('paths',     'OMFI:FL:Paths',     'list'),
    ]

    def read(self, f):
        super(FileLocator, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 2
        self.paths = []
        path = read_string(f)
        if path:
            self.path_name= path

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 76)
                path = read_string(f)
                if path:
                    self.paths.append(path)

            elif tag == 0x02:
                read_assert_tag(f, 76)
                # utf-8?
                path = read_string(f)
                if path:
                    self.paths.append(path)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class GraphicEffect(core.AVBObject):
    class_id = b'GRFX'
    properties = [
        AVBProperty('pict_data', 'OMFI:MC:GRFX:PictData', 'bytes'),
    ]
    def read(self, f):
        super(GraphicEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        pict_size = read_s32le(f)
        assert pict_size >= 0

        self.pict_data = bytearray(f.read(pict_size))
        assert len(self.pict_data) == pict_size

        read_assert_tag(f, 0x03)

@utils.register_class
class CFUserParam(core.AVBObject):
    class_id = b'AVUP'
    properties = [
        AVBProperty('byte_order', 'OMFI:AVUP:ByteOrder', 'uint16'),
        AVBProperty('uuid',       'OMFI:AVUP:TypeID',    'UUID'),
        AVBProperty('data',       'OMFI:AVUP:ValueData', 'bytes'),
    ]

    def read(self, f):
        super(CFUserParam, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.byte_order = read_s16le(f)
        assert self.byte_order == 0x4949

        self.uuid = read_raw_uuid(f)

        value_size = read_s32le(f)
        value_size = read_s32le(f)

        self.data = bytearray(f.read(value_size))

        read_assert_tag(f, 0x03)

@utils.register_class
class ParameterItems(core.AVBObject):
    class_id = b'PRIT'
    properties = [
        AVBProperty('uuid',            'OMFI:PRIT:GUID',                   'UUID'),
        AVBProperty('value_type',      'OMFI:PRIT:ValueType',              'int16'),
        AVBProperty('value',           'OMFI:PRIT:Value',                  'int32'),
        AVBProperty('name',            'OMFI:PRIT:Name',                   'string'),
        AVBProperty('enable',          'OMFI:PRIT:Enabled',                'bool'),
        AVBProperty('control_track',   'OMFI:PRIT:ControlTrack',           'reference'),
        AVBProperty('contribs_to_sig', 'OMFI:PRIT:ContributesToSignature', 'bool'),
    ]

    def read(self, f):
        super(ParameterItems, self).read(f)
        # print(peek_data(f).encode('hex'))
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        self.uuid = read_raw_uuid(f)
        self.value_type = read_s16le(f)
        if self.value_type == 1:
            self.value = read_s32le(f)
        elif self.value_type == 2:
            self.value = read_doublele(f)
        elif self.value_type == 4:
            self.value = read_object_ref(self.root, f)
        else:
            raise ValueError("unknown value_type: %d" % self.value_type)

        self.name = read_string(f)
        self.enable = read_bool(f)
        self.control_track = read_object_ref(self.root, f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 66)
                self.contribs_to_sig = read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class MSMLocator(core.AVBObject):
    class_id = b'MSML'
    properties = [
        AVBProperty('last_known_volume', 'OMFI:MSML:LastKnownVolume', 'string'),
        AVBProperty('domain_type',       'OMFI:MSML:DomainType',      'int32'),
        AVBProperty('mob_id',            'MobID',                     'MobID'),
    ]
    def read(self, f):
        super(MSMLocator, self).read(f)
        # print(peek_data(f).encode('hex'))
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)

        self.last_known_volume = read_string(f)

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 71)
                self.domain_type = read_s32le(f)
            elif tag == 0x02:
                mob_id = mobid.MobID()
                read_assert_tag(f, 65)
                length = read_s32le(f)
                assert length == 12
                mob_id.SMPTELabel = [read_byte(f) for i in range(12)]
                read_assert_tag(f, 68)
                mob_id.length = read_byte(f)
                read_assert_tag(f, 68)
                mob_id.instanceHigh = read_byte(f)
                read_assert_tag(f, 68)
                mob_id.instanceMid = read_byte(f)
                read_assert_tag(f, 68)
                mob_id.instanceLow = read_byte(f)
                read_assert_tag(f, 72)
                mob_id.Data1 = read_u32le(f)
                read_assert_tag(f, 70)
                mob_id.Data2 = read_u16le(f)
                read_assert_tag(f, 70)
                mob_id.Data3 = read_u16le(f)
                read_assert_tag(f, 65)
                length = read_s32le(f)
                assert length == 8
                mob_id.Data4 = [read_byte(f) for i in range(8)]
                self.mob_id = mob_id
            elif tag == 0x03:
                read_assert_tag(f, 76)
                length = read_s16le(f)
                assert length >= 0
                last_known_volume_utf8 = f.read(length)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class Position(core.AVBObject):
    class_id = b'APOS'
    properties = [
        AVBProperty('mob_id', "MobID", 'MobID'),
    ]

    def read(self, f):
        super(Position, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)

        self.mob_id = mobid.read_mob_id(f)

        if self.class_id ==  b'APOS':
            read_assert_tag(f, 0x03)


@utils.register_class
class BOBPosition(Position):
    class_id = b'ABOB'
    properties = Position.properties + [
        AVBProperty('sample_num',  "__OMFI:MSBO:sampleNum",   'int32'),
        AVBProperty('length',      "__OMFI:MSBO:length",      'int32'),
        AVBProperty('track_type',  "OMFI:trkt:Track.trkType", 'int32'),
        AVBProperty('track_index', "OMFI:trkt:Track.trkLNum", 'int32'),
    ]
    def read(self, f):
        super(BOBPosition, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.sample_num = read_s32le(f)
        self.length = read_s32le(f)
        self.track_type = read_s16le(f)
        self.track_index = read_s16le(f)

        if self.class_id ==  b'ABOB':
            read_assert_tag(f, 0x03)

@utils.register_class
class DIDPosition(BOBPosition):
    class_id = b'DIDP'
    properties = BOBPosition.properties + [
        AVBProperty('strip',        "_Strip",       'int32'),
        AVBProperty('offset',       "_Offset",      'uint64'),
        AVBProperty('byte_length',  "_ByteLength",  'uint64'),
        AVBProperty('spos_invalid', "_SPosInvalid", 'bool'),
    ]

    def read(self, f):
        super(DIDPosition, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.strip = read_s32le(f)
        self.offset = read_u64le(f)
        self.byte_length = read_u64le(f)
        self.spos_invalid = read_bool(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class BinRef(core.AVBObject):
    class_id = b'MCBR'
    properties = [
        AVBProperty('uid_high', 'OMFI:MCBR:MC:binID.high', 'int32'),
        AVBProperty('uid_low',  'OMFI:MCBR:MC:binID.low',  'int32'),
        AVBProperty('name',     'OMFI:MCBR:MC:binName',    'string'),
    ]
    def read(self, f):
        super(BinRef, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.uid_high = read_s32le(f)
        self.uid_low = read_s32le(f)
        self.name = read_string(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 76)
                length = read_s16le(f)
                assert length >= 0
                # always starts with '\x00\x00' ??
                name_utf8 = f.read(length)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class MobRef(core.AVBObject):
    class_id = b'MCMR'
    properties = [
            AVBProperty('position',      'OMFI:MCMR:MC:Position', 'int32'),
            AVBProperty('mob_id',        'MobID', 'MobID'),
    ]
    def read(self, f):
        super(MobRef, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        mob_hi = read_s32le(f)
        mob_lo = read_s32le(f)
        self.position = read_s32le(f)

        self.mob_id = mobid.read_mob_id(f)

        if self.class_id == b'MCMR':
            read_assert_tag(f, 0x03)

# also called a TimeCrumb
@utils.register_class
class Marker(MobRef):
    class_id = b'TMBC'
    properties = MobRef.properties + [
        AVBProperty('comp_offset',   'OMFI:TMBC:MC:CompOffset',             'int32'),
        AVBProperty('attributes',    'OMFI:TMBC:MC:Attributes',             'reference'),
        AVBProperty('color',         'OMFI:TMBC:MC:CarbonAPI::RGBColor',    'list'),
        AVBProperty('handled_codes', 'OMFI:TMBC:MC:handledBadControlCodes', 'bool'),
    ]

    def read(self, f):
        super(Marker, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        self.comp_offset = read_s32le(f)
        self.attributes = read_object_ref(self.root, f)
        # print(self.comp_offset, self.attributes)

        version = read_s16le(f)
        assert version == 1

        self.color = []
        self.color.append(read_s16le(f))
        self.color.append(read_s16le(f))
        self.color.append(read_s16le(f))

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 66)
                self.handled_codes = read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)
