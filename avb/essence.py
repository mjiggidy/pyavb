from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from io import BytesIO

from . import core
from . import utils
from .core import AVBProperty

from . utils import (
    read_byte,
    read_bool,
    read_s8,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_s64le,
    read_u64le,
    read_string,
    read_raw_uuid,
    read_uuid,
    reverse_str,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    iter_ext,
    read_assert_tag,
    peek_data
)

@utils.register_class
class MediaDescriptor(core.AVBObject):
    class_id = b'MDES'

    def read(self, f):
        super(MediaDescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        self.mob_kind = read_byte(f)
        self.locator = read_object_ref(self.root, f)
        self.intermediate = read_bool(f)
        self.locator = read_object_ref(self.root, f)

        # print('sss', self.locator)
        # print(peek_data(f).encode('hex'))

        self.uuid = None
        self.locator = None
        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 65)
                uuid_len = read_s32le(f)
                assert uuid_len == 16
                self.uuid = read_raw_uuid(f)
            elif tag == 0x03:
                read_assert_tag(f, 72)
                self.physical_media = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id == b'MDES':
            read_assert_tag(f, 0x03)

@utils.register_class
class TapeDescriptor(MediaDescriptor):
    class_id = b'MDTP'

class MediaFileDescriptor(MediaDescriptor):
    class_id = b'MDFL'

    def read(self, f):
        super(MediaFileDescriptor, self).read(f)

        tag = read_byte(f)

        # print peek_data(f).encode('hex')
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x03

        self.edit_rate = read_exp10_encoded_float(f)
        self.length = read_u32le(f)
        self.is_omfi = read_s16le(f)
        self.data_offset = read_u32le(f)

@utils.register_class
class PCMADescriptor(MediaFileDescriptor):
    class_id = b'PCMA'

    def read(self, f):
        super(PCMADescriptor, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.channels = read_u16le(f)
        self.quantization_bits = read_u16le(f)
        self.sample_rate = read_exp10_encoded_float(f)

        self.locked = read_bool(f)
        self.audio_ref_level = read_s16le(f)
        self.electro_spatial_formulation = read_u32le(f)
        self.dial_norm = read_u16le(f)

        self.coding_format = read_u32le(f)
        self.block_align = read_u32le(f)

        self.sequence_offset = read_u16le(f)
        self.average_bps = read_u32le(f)
        self.has_peak_envelope_data = read_bool(f)

        self.peak_envelope_version = read_s32le(f)
        self.peak_envelope_format = read_s32le(f)
        self.points_per_peak_value = read_s32le(f)
        self.peak_envelope_block_size = read_s32le(f)
        self.peak_channel_count = read_s32le(f)
        self.peak_frame_count = read_s32le(f)
        self.peak_of_peaks_offset = read_u64le(f)
        self.peak_envelope_timestamp = read_s32le(f)

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class DIDDescriptor(MediaFileDescriptor):
    class_id = b'DIDD'

    def read(self, f):
        super(DIDDescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x02

        self.stored_height = read_s32le(f)
        self.stored_width  = read_s32le(f)

        self.sampled_height = read_s32le(f)
        self.sampled_width  = read_s32le(f)

        self.sampled_x_offset = read_s32le(f)
        self.sampled_y_offset = read_s32le(f)

        self.display_height = read_s32le(f)
        self.display_width  = read_s32le(f)

        self.display_x_offset = read_s32le(f)
        self.display_y_offset = read_s32le(f)

        self.frame_layout = read_s16le(f)

        numerator = read_s32le(f)
        denominator = read_s32le(f)
        self.aspect_ratio = [numerator, denominator]

        line_map_byte_size = read_s32le(f)
        self.line_map = []
        if line_map_byte_size:
            for i in range(line_map_byte_size // 4):
                v = read_s32le(f)
                self.line_map.append(v)

        self.alpha_transparency = read_s32le(f)
        self.uniformness = read_bool(f)

        self.did_image_size = read_s32le(f)

        self.next_did_desc = read_object_ref(self.root, f)

        self.compress_method = reverse_str(f.read(4))

        self.resolution_id = read_s32le(f)
        self.image_alignment_factor =  read_s32le(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 69)
                self.frame_index_byte_order = read_s16le(f)

            elif tag == 0x02:
                read_assert_tag(f, 71)
                self.frame_sample_size = read_s32le(f)

            elif tag == 0x03:
                read_assert_tag(f, 71)
                self.first_frame_offset = read_s32le(f)

            elif tag == 0x04:
                read_assert_tag(f, 71)
                self.client_fill_start = read_s32le(f)

                read_assert_tag(f, 71)
                self.client_fill_end = read_s32le(f)

            elif tag == 0x05:
                read_assert_tag(f, 71)
                self.offset_to_rle_frame_index = read_s32le(f)

            elif tag == 0x08:
                # valid
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_x = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_y = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_width = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_height = [x, y]

                # essence
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_x = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_y = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_width = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_height = [x, y]

                # source
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_x = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_y = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_width = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.souce_height = [x, y]

            elif tag == 9:
                # print("\n??!", peek_data(f).encode('hex'), '\n')
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_x = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_y = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_width = [x, y]

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_height = [x, y]

                read_assert_tag(f, 71)
                self.reformatting_option = read_s32le(f)

            elif tag == 10:
                read_assert_tag(f, 80)
                self.transfer_characteristic = read_raw_uuid(f)
            elif tag == 11:
                read_assert_tag(f, 80)
                self.color_primaries =  read_raw_uuid(f)
                read_assert_tag(f, 80)
                self.coding_equations = read_raw_uuid(f)

            elif tag == 15:
                read_assert_tag(f, 66)
                self.frame_sample_size_has_been_checked_with_mapper = read_bool(f)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id == b'DIDD':
            read_assert_tag(f, 0x03)

@utils.register_class
class CDCIDescriptor(DIDDescriptor):
    class_id = b'CDCI'

    def read(self, f):
        super(CDCIDescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x02

        self.horizontal_subsampling = read_u32le(f)
        self.vertical_subsampling = read_u32le(f)
        self.component_width = read_u32le(f)

        self.color_sitting = read_s16le(f)
        self.black_ref_level = read_u32le(f)
        self.white_ref_level = read_u32le(f)
        self.color_range = read_u32le(f)

        self.offset_to_frames64 = read_s64le(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 72)
                self.alpha_sampled_width = read_u32le(f)

            elif tag == 0x02:
                read_assert_tag(f, 72)
                self.ignore_bw_ref_level_and_color_range = read_u32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03


def decode_pixel_layout(pixel_layout, pixel_struct):

    layout = []
    for i in range(8):
        code = read_byte(pixel_layout)
        depth = read_byte(pixel_struct)
        if not code:
            break
        layout.append({'Code':code, 'Size':depth})

    return layout

@utils.register_class
class RGBADescriptor(DIDDescriptor):
    class_id = b'RGBA'

    def read(self, f):
        super(RGBADescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        # this seems to be encode the same way as in AAF
        layout_size = read_u32le(f)
        pixel_layout = BytesIO(f.read(layout_size))

        struct_size =  read_u32le(f)
        pixel_struct = BytesIO(f.read(struct_size))

        self.pixel_layout = decode_pixel_layout(pixel_layout, pixel_struct)

        # print([self.pixel_struct])

        palette_layout_size = read_u32le(f)
        assert palette_layout_size == 0

        palette_struct_size = read_u32le(f)
        assert palette_struct_size == 0

        palette_size = read_u32le(f)
        assert palette_size == 0

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 77)
                self.offset_to_frames64 = read_u64le(f)

            elif tag == 0x02:
                read_assert_tag(f, 66)
                self.has_comp_min_ref = read_bool(f)

                read_assert_tag(f, 72)
                self.comp_min_ref = read_u32le(f)

                read_assert_tag(f, 66)
                self.has_comp_max_ref = read_bool(f)

                read_assert_tag(f, 72)
                self.comp_max_ref = read_u32le(f)

            elif tag == 0x03:
                read_assert_tag(f, 72)
                self.alpha_min_ref = read_u32le(f)

                read_assert_tag(f, 72)
                self.alpha_max_ref = read_u32le(f)

            else:
                raise ValueError("unknown ext tag 0x%02X %d" % (tag,tag))

        tag = read_byte(f)
        assert tag == 0x03
