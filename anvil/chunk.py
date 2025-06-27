from collections.abc import Generator
from nbt import nbt
from .block import Block, OldBlock
from .region import Region
from .errors import OutOfBoundsCoordinates, ChunkNotFound, EmptyRegionFile
from .utils import bin_append, nibble

# Last Checked Version: 1.20.2-rc2
# ----------------------------------------------------------------------------------------------------
# Data Versions - https://minecraft.wiki/w/Data_version
# Anvil Format - https://minecraft.wiki/w/Anvil_file_format
# Chunk Format - https://minecraft.wiki/w/Chunk_format
# ----------------------------------------------------------------------------------------------------
# NBT Format - https://minecraft.wiki/w/NBT_format
# Entity Format - https://minecraft.wiki/w/Entity_format
# Player.dat Format - https://minecraft.wiki/w/Player.dat_format (note 23w32a changes the player.dat format)
# Level.dat Format - https://minecraft.wiki/w/Java_Edition_level_format#level.dat_format
# Structure File Format - https://minecraft.wiki/w/Structure_Block_file_format
# POI Format - https://minecraft.wiki/w/Point_of_Interest
# Villages.dat Format - https://minecraft.wiki/w/Villages.dat_format
# Raids.dat Format - https://minecraft.wiki/w/Raids.dat_format
# Map Format - https://minecraft.wiki/w/Map_item_format
# Servers.dat Format - https://minecraft.wiki/w/Servers.dat_format
# Schematic File Format (Unofficial) - https://minecraft.wiki/w/Schematic_file_format


# Chunk Format Changed - https://minecraft.wiki/w/Java_Edition_21w43a
# Removed the Level tag and moved everything up a level (e.g. Level.TileEntities to block_entities)
_VERSION_21w43a = 2844

# Chunk Format Changed - https://minecraft.wiki/w/Java_Edition_21w39a
# Chunk tags were renamed and had their data type changed too (e.g. BlockStates to block_states)
_VERSION_21w39a = 2836

# Build Height Limit Decrease - https://minecraft.wiki/w/Java_Edition_21w15a
# Build height limit reverted back to 256 blocks (0 to 255) from version 21w06a
_VERSION_21w15a = 2709

# Build Height Limit Increase - https://minecraft.wiki/w/Java_Edition_21w06a
# Build height limit increased to 384 blocks (-64 to 319)
_VERSION_21w06a = 2694

# Entity Format Changed - https://minecraft.wiki/w/Java_Edition_20w45a
# Moved entity data to its own folder from terrain data
_VERSION_20w45a = 2681

# Block Storage Format Changed - https://minecraft.wiki/w/Java_Edition_20w17a
# This version removes block state value stretching from the storage
# so a block value isn't in multiple elements of the array
_VERSION_20w17a = 2529

# Added POI Folder - https://minecraft.wiki/w/Java_Edition_19w11a
# Villages and other points of interest are now in a poi folder
#   instead of being in its own separate files
_VERSION_19w11a = 1937

# Block Format Changed - https://minecraft.wiki/w/Java_Edition_17w47a
# This is the version where "The Flattening" (https://minecraft.wiki/w/Java_Edition_1.13/Flattening) happened
# where blocks went from numeric ids to namespaced ids (namespace:block_id)
_VERSION_17w47a = 1451

# This was the version that introduced the anvil format and added customizable build height
# There is no version number as this was prior to data versions being introduced
# Data versions were introduced with 15w32a (1.9 snapshot) and started at 100
# _VERSION_12w07a = -1

class Chunk:
    """
    Represents a chunk from a ``.mca`` file.

    Note that this is read only.

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    lowest_y: :class:`int`
        Chunk's lowest Y position
    highest_y: :class:`int`
        Chunk's highest Y position
    version: :class:`int`
        Version of the chunk NBT structure
    data: :class:`nbt.TAG_Compound`
        Raw NBT data of the chunk
    guessed_type: :class:`string`
        The guess for the type of chunk data we're looking at
    block_entities: :class:`nbt.TAG_Compound`
        ``self.data['TileEntities']`` as an attribute for easier use (or ``self.data['block_entities']`` if chunk's world's version is at least 21w43a)
    entities: :class:`nbt.TAG_Compound`
        ``self.data['Entities']`` as an attribute for easier use (or ``self.data['block_entities']`` if chunk's world's version is at least 21w43a)
    """
    __slots__ = ('version', 'data', 'x', 'z', 'lowest_y', 'highest_y', 'block_entities', 'tile_entities')

    def __init__(self, nbt_data: nbt.NBTFile):
        try:
            self.version = nbt_data['DataVersion'].value
        except KeyError:
            # Version is pre-1.9 snapshot 15w32a, so world does not have a Data Version.
            # See https://minecraft.wiki/w/Data_version
            self.version = None

        self.data = nbt_data

        # Base data expected to be in any region file (citation needed)
        self.x = self.data['Level']['xPos'].value
        self.z = self.data['Level']['zPos'].value
        self.lowest_y = self.get_lowest_section()
        self.highest_y = self.get_highest_section()

        # Scan for block entity tag and set easy use attributes
        self.tile_entities: nbt.TAG_List | None = None
        self.block_entities: nbt.TAG_List | None = None
        self.init_block_entities(nbt_data=nbt_data)

        # print("(X: %s, Z: %s, L: %s, H: %s)" % (self.x, self.z, self.lowest_y, self.highest_y))

    def init_block_entities(self, nbt_data: nbt.NBTFile):
        # We may be reading a chunk that holds entities or something else,
        #   so block entities may not exist in this data
        try:
            if self.version and self.version >= _VERSION_21w43a:
                self.data = nbt_data
                self.tile_entities = self.data['block_entities']
            else:
                self.data = nbt_data['Level']
                self.tile_entities = self.data['TileEntities']
        except KeyError:
            # We're reading something without block entities
            self.tile_entities = None

        # to match the rename. we aren't getting rid of tile_entities, just making sure there's a match with the modern term
        self.block_entities = self.tile_entities

    def init_entities(self, nbt_data: nbt.NBTFile):
        try:
            if self.version and self.version >= _VERSION_21w43a:
                self.data = nbt_data
                self.tile_entities = self.data['block_entities']
            else:
                self.data = nbt_data['Level']
                self.tile_entities = self.data['TileEntities']
        except KeyError:
            # We're reading something without block entities
            self.tile_entities = None

        # to match the rename. we aren't getting rid of tile_entities, just making sure there's a match with the modern term
        self.block_entities = self.tile_entities

    def get_lowest_section(self) -> int | None:
        try:
            if self.version and self.version >= _VERSION_21w43a:
                sections = self.data['sections']
            else:
                sections = self.data['Sections']
        except KeyError:
            return None

        if self.version and self.version >= _VERSION_21w43a:
            return self.data['yPos'].value

        if len(sections) < 1:
            raise EmptyRegionFile('The section array is empty. There\'s no data to process')
        
        return sections[0]['Y'].value

    def get_highest_section(self) -> int | None:
        try:
            if self.version and self.version >= _VERSION_21w43a:
                sections = self.data['sections']
            else:
                sections = self.data['Sections']
        except KeyError:
            return None

        if len(sections) < 1:
            raise EmptyRegionFile('The section array is empty. There\'s no data to process')

        return sections[-1]['Y'].value

    def get_section(self, y: int) -> nbt.TAG_Compound | None:
        """
        Returns the section at given y index
        can also return nothing if section is missing, aka it's empty

        Parameters
        ----------
        y
            Section Y index

        Raises
        ------
        anvil.OutOfBoundsCoordinates
            If Y is not in range of self.lowest_y to self.highest_y
        """
        if (self.lowest_y and y < self.lowest_y) or (self.highest_y and y > self.highest_y):
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of {self.lowest_y!r} to {self.highest_y!r}')

        try:
            # print("Data: %s" % self.data)

            if self.version and self.version >= _VERSION_21w43a:
                sections = self.data['sections']
            else:
                sections = self.data['Sections']
        except KeyError:
            return None

        for section in sections:
            if section['Y'].value == y:
                return section

    def get_palette(self, section: int | nbt.TAG_Compound) -> tuple[Block, ...] | None:
        """
        Returns the block palette for given section

        Parameters
        ----------
        section
            Either a section NBT tag or an index

        :rtype: tuple[:class:`anvil.Block`]
        """
        if isinstance(section, int):
            section = self.get_section(section)
        if section is None:
            return None

        # print("Section: %s" % section)
        if self.version and self.version >= _VERSION_21w39a:
            palette_parent = section['block_states']
        else:
            palette_parent = section

        if self.version and self.version >= _VERSION_21w43a:
            palette_tag = 'palette'
        else:
            palette_tag = 'Palette'

        # print("palette_parent: %s" % palette_parent)
        return tuple(Block.from_palette(i) for i in palette_parent[palette_tag])

    def get_block(self, x: int, y: int, z: int, section: int | nbt.TAG_Compound | None = None, force_new: bool=False) -> Block | OldBlock | None:
        """
        Returns the block in the given coordinates

        Parameters
        ----------
        int x, y, z
            Block's coordinates in the chunk
        section : int
            Either a section NBT tag or an index. If no section is given,
            assume Y is global and use it for getting the section.
        force_new
            Always returns an instance of Block if True, otherwise returns type OldBlock for pre-1.13 versions.
            Defaults to False

        Raises
        ------
        anvil.errors.OutOfBoundCoordinates
            If X, Y or Z are not in the proper range

        :rtype: :class:`anvil.Block`
        """
        lowest_bound = self.lowest_y * 16 if self.lowest_y is not None else float('-inf')
        highest_bound = self.highest_y * 16 if self.highest_y is not None else float('inf')
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < lowest_bound or y > highest_bound:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of {lowest_bound!r} to {highest_bound!r}')

        if section is None:
            section = self.get_section(y // 16)
            # global Y to section Y
            y %= 16

        if self.version is None or self.version < _VERSION_17w47a:
            # Explained in depth here https://minecraft.gamepedia.com/index.php?title=Chunk_format&oldid=1153403#Block_format
            if section is None:
                if force_new:
                    return Block.from_name('minecraft:air')
                else:
                    return OldBlock(0)

            # Handle case where section is an int
            if isinstance(section, int):
                section = self.get_section(section)
                if section is None:
                    if force_new:
                        return Block.from_name('minecraft:air')
                    else:
                        return OldBlock(0)

            index = y * 16 * 16 + z * 16 + x

            block_id = section['Blocks'][index]
            if 'Add' in section:
                block_id += nibble(section['Add'], index) << 8

            block_data = nibble(section['Data'], index)
            block = OldBlock(block_id, block_data)

            if force_new:
                return block.convert()
            else:
                return block

        # Convert int section index to actual section
        if isinstance(section, int):
            section = self.get_section(section)

        if section is None:
            return None

        block_states_tag = 'block_states'
        if self.version >= _VERSION_21w39a:
            palette_parent = section[block_states_tag]
        else:
            block_states_tag = 'BlockStates'
            palette_parent = section

        if self.version >= _VERSION_21w43a:
            palette_tag = 'palette'
        else:
            palette_tag = 'Palette'

        # If its an empty section its most likely an air block
        # print("Section: %s" % section)
        if section is None or block_states_tag not in section:
            return Block.from_name('minecraft:air')

        # Number of bits each block is on BlockStates
        # Cannot be lower than 4
        if self.version >= _VERSION_21w39a:
            bits = max((len(section[block_states_tag][palette_tag]) - 1).bit_length(), 4)
        else:
            bits = max((len(section[palette_tag]) - 1).bit_length(), 4)

        # Get index on the block list with the order YZX
        index = y * 16*16 + z * 16 + x

        # BlockStates is an array of 64 bit numbers
        # that holds the blocks index on the palette list
        # Confirmed: 21w39a moved BlockStates & Palette to block_states container structure
        # Source: https://feedback.minecraft.net/hc/en-us/articles/4410294651405-Minecraft-Java-Edition-Snapshot-21w39a
        if self.version >= _VERSION_21w39a:
            # If its an empty section its most likely an air block
            if 'data' not in section[block_states_tag]:
                return Block.from_name('minecraft:air')

            states = section[block_states_tag]['data'].value
        else:
            states = section[block_states_tag].value
        # print("States: %s" % states)

        # in 20w17a and newer blocks cannot occupy more than one element on the BlockStates array
        stretches = self.version is None or self.version < _VERSION_20w17a
        # stretches = True

        # get location in the BlockStates array via the index
        if stretches:
            state = index * bits // 64
        else:
            state = index // (64 // bits)

        # makes sure the number is unsigned
        # by adding 2^64
        # could also use ctypes.c_ulonglong(n).value but that'd require an extra import
        # print("State: %s" % state)
        data = states[state]
        if data < 0:
            data += 2**64

        if stretches:
            # shift the number to the right to remove the left over bits
            # and shift so the i'th block is the first one
            shifted_data = data >> ((bits * index) % 64)
        else:
            shifted_data = data >> (index % (64 // bits) * bits)

        # if there aren't enough bits it means the rest are in the next number
        if stretches and 64 - ((bits * index) % 64) < bits:
            data = states[state + 1]
            if data < 0:
                data += 2**64

            # get how many bits are from a palette index of the next block
            leftover = (bits - ((state + 1) * 64 % bits)) % bits

            # Make sure to keep the length of the bits in the first state
            # Example: bits is 5, and leftover is 3
            # Next state                Current state (already shifted)
            # 0b101010110101101010010   0b01
            # will result in bin_append(0b010, 0b01, 2) = 0b01001
            shifted_data = bin_append(data & 2**leftover - 1, shifted_data, bits-leftover)

        # get `bits` least significant bits
        # which are the palette index
        palette_id = shifted_data & 2**bits - 1

        # print("Block: %s" % palette_parent[palette_tag][palette_id])
        block = palette_parent[palette_tag][palette_id]
        return Block.from_palette(block)

    def stream_blocks(
            self, 
            index: int = 0, 
            section: int | nbt.TAG_Compound | None = None, 
            force_new: bool = False
    ) -> Generator[Block | OldBlock, None, None]:
        """
        Returns a generator for all the blocks in given section

        Parameters
        ----------
        index
            At what block to start from.

            To get an index from (x, y, z), simply do:

            ``y * 256 + z * 16 + x``
        section
            Either a Y index or a section NBT tag.
        force_new
            Always returns an instance of Block if True, otherwise returns type OldBlock for pre-1.13 versions.
            Defaults to False

        Raises
        ------
        anvil.errors.OutOfBoundCoordinates
            If `section` is not in the range of 0 to 15

        Yields
        ------
        :class:`anvil.Block`
        """
        if isinstance(section, int) and (section < 0 or section > 16):
            raise OutOfBoundsCoordinates(f'section ({section!r}) must be in range of 0 to 15')

        # For better understanding of this code, read get_block()'s source

        if section is None or isinstance(section, int):
            section = self.get_section(section or 0)

        if self.version and self.version < _VERSION_17w47a:
            if section is None or 'Blocks' not in section:
                air = Block.from_name('minecraft:air') if force_new else OldBlock(0)
                for _ in range(4096):
                    yield air
                return

            while index < 4096:
                block_id = section['Blocks'][index]
                if 'Add' in section:
                    block_id += nibble(section['Add'], index) << 8

                block_data = nibble(section['Data'], index)

                block = OldBlock(block_id, block_data)
                if force_new:
                    yield block.convert()
                else:
                    yield block

                index += 1
            return

        # Convert int section index to actual section
        if isinstance(section, int):
            section = self.get_section(section)

        if section is None:
            return None

        if self.version and self.version >= _VERSION_21w39a:
            block_states_tag = 'block_states'
            palette_parent = section[block_states_tag]
        else:
            block_states_tag = 'BlockStates'
            palette_parent = section

        if self.version and self.version >= _VERSION_21w43a:
            palette_tag = 'palette'
        else:
            palette_tag = 'Palette'

        if section is None or block_states_tag not in section:
            air = Block.from_name('minecraft:air')
            for _ in range(4096):
                yield air
            return

        states = section[block_states_tag].value
        palette = palette_parent[palette_tag]

        bits = max((len(palette) - 1).bit_length(), 4)

        if self.version:
            stretches = self.version < _VERSION_20w17a
        else:
            stretches = None

        if stretches:
            state = index * bits // 64
        else:
            state = index // (64 // bits)

        data = states[state]
        if data < 0:
            data += 2**64

        bits_mask = 2**bits - 1

        if stretches:
            offset = (bits * index) % 64
        else:
            offset = index % (64 // bits) * bits

        data_len = 64 - offset
        data >>= offset

        while index < 4096:
            if data_len < bits:
                state += 1
                new_data = states[state]
                if new_data < 0:
                    new_data += 2**64

                if stretches:
                    leftover = data_len
                    data_len += 64

                    data = bin_append(new_data, data, leftover)
                else:
                    data = new_data
                    data_len = 64

            palette_id = data & bits_mask
            yield Block.from_palette(palette[palette_id])

            index += 1
            data >>= bits
            data_len -= bits

    def stream_chunk(self, index: int = 0) -> Generator[Block | OldBlock, None, None]:
        """
        Returns a generator for all the blocks in the chunk

        This is a helper function that runs Chunk.stream_blocks from section 0 to 15

        Yields
        ------
        :class:`anvil.Block`
        """
        lower_bound = self.lowest_y if self.lowest_y else 0
        upper_bound = self.highest_y if self.highest_y else 15

        for section_y in range(lower_bound, upper_bound + 1):
            for block in self.stream_blocks(index=index, section=section_y):
                yield block

    def get_tile_entity(self, x: int, y: int, z: int) -> nbt.TAG_Compound | None:
        return self.get_block_entity(x, y, z)

    def get_block_entity(self, x: int, y: int, z: int) -> nbt.TAG_Compound | None:
        """
        Returns the block entity at given coordinates, or ``None`` if there isn't a block entity

        To iterate through all block entities in the chunk, use :class:`Chunk.block_entities`
        """
        if self.block_entities:
            for block_entity in self.block_entities:
                b_x, b_y, b_z = [block_entity[k].value for k in 'xyz']
                if x == b_x and y == b_y and z == b_z:
                    return block_entity
        return None

    @classmethod
    def from_region(cls, region: str | Region, chunk_x: int, chunk_z: int):
        """
        Creates a new chunk from region and the chunk's X and Z

        Parameters
        ----------
        region
            Either a :class:`anvil.Region` or a region file name (like ``r.0.0.mca``)

        Raises
        ----------
        anvil.ChunkNotFound
            If a chunk is outside this region or hasn't been generated yet
        """
        if isinstance(region, str):
            region = Region.from_file(region)
        nbt_data = region.chunk_data(chunk_x, chunk_z)
        if nbt_data is None:
            raise ChunkNotFound(f'Could not find chunk ({chunk_x}, {chunk_z})')
        return cls(nbt_data)
