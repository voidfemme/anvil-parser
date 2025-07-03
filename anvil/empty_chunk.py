from .block import Block
from .empty_section import EmptySection
from .raw_section import RawSection
from .errors import OutOfBoundsCoordinates, EmptySectionAlreadyExists
from nbt import nbt

# TODO: Determine if should update this file to modern Minecraft
class EmptyChunk:
    """
    Used for making own chunks

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    sections: list[:class:`anvil.EmptySection`]
        list of all the sections in this chunk
    version: :class:`int`
        Chunk's DataVersion
    """
    __slots__ = ('x', 'z', 'sections', 'version')
    def __init__(self, x: int, z: int) -> None:
        self.x = x
        self.z = z
        self.sections: list[EmptySection | None] = [None]*16
        self.version = 1976

    def add_section(self, section: EmptySection | RawSection, replace: bool = True) -> None:
        """
        Adds a section to the chunk

        Parameters
        ----------
        section
            Section to add
        replace
            Whether to replace section if one at same Y already exists
        
        Raises
        ------
        anvil.EmptySectionAlreadyExists
            If ``replace`` is ``False`` and section with same Y already exists in this chunk
        """
        if self.sections[section.y] and not replace:
            raise EmptySectionAlreadyExists(f'EmptySection (Y={section.y}) already exists in this chunk')
        self.sections[section.y] = section

    def get_block(self, x: int, y: int, z: int) -> Block | None:
        """
        Gets the block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of 0 to 255

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        Returns
        -------
        block : :class:`anvil.Block` or None
            Returns ``None`` if the section is empty, meaning the block
            is most likely an air block.
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        # Anvil has always allowed custom world heights
        # if y < 0 or y > 255:
        #     raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')

        section = self.sections[y // 16]
        if section is None:
            return None
        return section.get_block(x, y % 16, z) # type: ignore

    def set_block(self, block: Block, x: int, y: int, z: int) -> None:
        """
        Sets block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of 0 to 255

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range
        
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        # Anvil has always allowed custom world heights
        # if y < 0 or y > 255:
        #     raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')

        section = self.sections[y // 16]
        if section is None:
            section = EmptySection(y // 16)
            self.add_section(section)
        section.set_block(block, x, y % 16, z) # type: ignore

    def save(self) -> nbt.NBTFile:
        """
        Saves the chunk data to a :class:`NBTFile`

        Notes
        -----
        Does not contain most data a regular chunk would have,
        but minecraft stills accept it.
        """
        root = nbt.NBTFile()
        root.tags.append(nbt.TAG_Int(name='DataVersion',value=self.version))
        level = nbt.TAG_Compound()
        # Needs to be in a separate line because it just gets
        # ignored if you pass it as a kwarg in the constructor
        level.name = 'Level'
        level.tags.extend([
            nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
            nbt.TAG_List(name='TileEntities', type=nbt.TAG_Compound),
            nbt.TAG_List(name='LiquidTicks', type=nbt.TAG_Compound),
            nbt.TAG_Int(name='xPos', value=self.x),
            nbt.TAG_Int(name='zPos', value=self.z),
            nbt.TAG_Long(name='LastUpdate', value=0),
            nbt.TAG_Long(name='InhabitedTime', value=0),
            nbt.TAG_Byte(name='isLightOn', value=1),
            nbt.TAG_String(name='Status', value='full')
        ])
        sections = nbt.TAG_List(name='Sections', type=nbt.TAG_Compound)
        for s in self.sections:
            if s:
                p = s.palette()
                # Minecraft does not save sections that are just air
                # So we can just skip them
                if len(p) == 1 and p[0] and p[0].name() == 'minecraft:air':
                    continue
                sections.tags.append(s.save())
        level.tags.append(sections)
        root.tags.append(level)
        return root
