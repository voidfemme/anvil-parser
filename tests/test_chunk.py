import context as _
from anvil import Chunk, Region
from anvil.errors import GZipChunkData, CorruptedData

# TODO: Implement tests for anvil/chunk.py
#
# TestChunk class:
#   - A test for get_block() that checks a variety of coordinates and block types.
#   - A test for get_block() on a pre-1.13 chunk to ensure it returns an OldBlock instance (or a Block if force_new=True).
#   - A test for get_block_entity() to verify it can find and return a block entity from a chunk.
#   - A test that attempts to read a chunk from a region that uses GZip compression to ensure the GZipChunkData exception is raised.
#   - A test that attempts to read a corrupted chunk to ensure the CorruptedData exception is raised.
#   - Tests for the version-specific logic. This is the most critical and complex part. You would need to create or find region files from different Minecraft versions (especially around the "Flattening" and the 20w17a snapshot) and write tests to ensure that get_block and other methods correctly parse the data.
