from abc import ABC, abstractmethod
from nbt import nbt
from . import Block
import array

class BaseSection(ABC):
    def __init__(self, y: int):
        self.y = y

    @abstractmethod
    def palette(self) -> tuple[Block | None, ...]:
        """
        Generates and returns a tuple of all the different blocks in the section
        The order can change as it uses sets, but should be fine when saving since
        it's only called once.
        """
        pass

    @abstractmethod
    def blockstates(self, palette: tuple[Block | None, ...] | None = None) -> array.array:
        """
        Returns a list of each block's index in the palette.
        
        This is used in the BlockStates tag of the section.

        Parameters
        ----------
        palette
            Section's palette. If not given will generate one.
        """
        pass

    def save(self) -> nbt.TAG_Compound:
        """
        Saves the section to a TAG_Compound and is used inside the chunk tag
        This is missing the SkyLight tag, but minecraft still accepts it anyway
        """
        root = nbt.TAG_Compound()
        root.tags.append(nbt.TAG_Byte(name='Y', value=self.y))

        palette = self.palette()
        nbt_pal = nbt.TAG_List(name='Palette', type=nbt.TAG_Compound)
        for block in palette:
            if block is None:
                continue

            tag = nbt.TAG_Compound()
            tag.tags.append(nbt.TAG_String(name='Name', value=block.name()))
            if block.properties:
                properties = nbt.TAG_Compound()
                properties.name = 'Properties'
                for key, value in block.properties.items():
                    if isinstance(value, str):
                        properties.tags.append(nbt.TAG_String(name=key, value=value))
                    elif isinstance(value, bool):
                        # booleans are a string saved as either 'true' or 'false'
                        properties.tags.append(nbt.TAG_String(name=key, value=str(value).lower()))
                    elif isinstance(value, int):
                        # ints also seem to be saved as a string
                        properties.tags.append(nbt.TAG_String(name=key, value=str(value)))
                    else:
                        # assume its a nbt tag and just append it
                        properties.tags.append(value)
                tag.tags.append(properties)
            nbt_pal.tags.append(tag)
        root.tags.append(nbt_pal)

        states = self.blockstates(palette=palette)
        bstates = nbt.TAG_Long_Array(name='BlockStates')
        bstates.value = states.tolist()
        root.tags.append(bstates)

        return root
