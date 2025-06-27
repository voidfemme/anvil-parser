from struct import Struct

# Dirty mixin to change q to Q
def _update_fmt(self, length: int) -> None:
    self.fmt = Struct(f'>{length}Q')

def bin_append(a: int, b: int, length: int | None = None) -> int:
    length = length or b.bit_length()
    return (a << length) | b

def nibble(byte_array: bytearray, index: int) -> int:
    value = byte_array[index // 2]
    if index % 2:
        return value >> 4
    else:
        return value & 0b1111
