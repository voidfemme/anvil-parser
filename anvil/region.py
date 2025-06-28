from pathlib import Path
from typing import BinaryIO
from nbt import nbt
import zlib
from io import BytesIO
import anvil
from .errors import GZipChunkData, EmptyRegionFile, CorruptedData, InvalidFileType

class Region:
    """
    Read-only region

    Attributes
    ----------
    data: :class:`bytes`
        Region file (``.mca``) as bytes

    Raises
        ------
        anvil.errors.EmptyRegionFile
            If region file has no data to process
    """
    __slots__ = ('data',)
    def __init__(self, data: bytes):
        """Makes a Region object from data, which is the region file content"""
        if not data:
            self.data = None
            raise EmptyRegionFile('Region file is empty. There\'s no data to process')

        self.data = data

    @staticmethod
    def header_offset(chunk_x: int, chunk_z: int) -> int:
        """
        Returns the byte offset for given chunk in the header
        
        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        return 4 * (chunk_x % 32 + chunk_z % 32 * 32)

    def chunk_location(self, chunk_x: int, chunk_z: int) -> tuple[int, int] | None:
        """
        Returns the chunk offset in the 4KiB sectors from the start of the file,
        and the length of the chunk in sectors of 4KiB

        Will return ``(0, 0)`` if chunk hasn't been generated yet

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        b_off = self.header_offset(chunk_x, chunk_z)
        if self.data:
            off = int.from_bytes(self.data[b_off : b_off + 3], byteorder='big')
            sectors = self.data[b_off + 3]
            return (off, sectors)
        else:
            raise EmptyRegionFile('Region file is empty. There\' no data to process')

    def chunk_data(self, chunk_x: int, chunk_z: int) -> nbt.NBTFile | None:
        """
        Returns the NBT data for a chunk
        
        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value

        Raises
        ------
        anvil.GZipChunkData
            If the chunk's compression is gzip
        """
        off = self.chunk_location(chunk_x, chunk_z)

        # (0, 0) means it hasn't generated yet, aka it doesn't exist yet
        if off is None or off == (0, 0):
            return None

        off = off[0] * 4096
        if self.data:
            length = int.from_bytes(self.data[off:off + 4], byteorder='big')
            compression = self.data[off + 4] # 2 most of the time

            if compression == 1:
                raise GZipChunkData('GZip is not supported')

            compressed_data = self.data[off + 5 : off + 5 + length - 1]
            decompressed_data = zlib.decompress(compressed_data)
        else:
            raise EmptyRegionFile('Region file is empty. There\'s no data to process')

        try:
            nbt_data = nbt.NBTFile(buffer=BytesIO(decompressed_data))
        except UnicodeDecodeError:
            # with open("corrupted.nbt", "wb") as corrupted_nbt_data:
            #     corrupted_nbt_data.write(decompressed_data)
                
            raise CorruptedData({'message':'Failed to read decompressed NBT data with UnicodeDecodeError','data':decompressed_data})
        except Exception:
            raise CorruptedData({'message':'Failed to read decompressed NBT data','data':decompressed_data})

        return nbt_data

    def get_chunk(self, chunk_x: int, chunk_z: int) -> 'anvil.Chunk':
        """
        Returns the chunk at given coordinates,
        same as doing ``Chunk.from_region(region, chunk_x, chunk_z)``

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        
        
        :rtype: :class:`anvil.Chunk`
        """
        return anvil.Chunk.from_region(self, chunk_x, chunk_z)

    @classmethod
    def from_file(cls, file: str | BinaryIO | Path) -> 'anvil.Region':
        """
        Creates a new region with the data from reading the given file

        Parameters
        ----------
        file
            Either a file path or a file object
        """
        if isinstance(file, (str, Path)):
            with open(file, 'rb') as f:
                return cls(data=f.read())
        elif hasattr(file, 'read'):
            return cls(data=file.read())
        else:
            raise InvalidFileType({
                'message':f"Expected str, Path, or file-like object, got {type(file).__name__}",
                'data' : file
            })
