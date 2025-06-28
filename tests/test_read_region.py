from anvil.errors import EmptyRegionFile
from anvil.empty_region import EmptyRegion
from anvil.empty_chunk import EmptyChunk
import context as _
import pytest
from anvil import Region
import io
import secrets

# TODO: Implement tests for anvil/region.py
#
# TestRegion class:
#   - A test for chunk_location() to ensure it returns the correct offset and sector count for a given chunk.
#   - A test for chunk_location() on a non-existent chunk to ensure it returns `(0, 0)`.
#   - A test for chunk_data() on a non-existent chunk to ensure it returns `None`.

def test_from_filename(tmp_path) -> None:
    filename = tmp_path / "region.mca"
    contents = secrets.token_bytes()

    with open(filename, 'wb') as f:
        f.write(contents)

    region = Region.from_file(str(filename))
    assert region.data == contents

def test_from_filelike() -> None:
    contents = secrets.token_bytes()
    filelike = io.BytesIO(contents)

    region = Region.from_file(filelike)
    assert region.data == contents

def test_chunk_location_existing_chunk() -> None:
    # Create region with a chunk
    empty_region = EmptyRegion(0, 0)
    chunk = EmptyChunk(0, 0)
    empty_region.add_chunk(chunk)

    # Convert to Region
    region_bytes = empty_region.save()
    region = Region(region_bytes)

    result = region.chunk_location(0, 0)
    if result is None:
        offset, sectors = 0, 0
    else:
        offset, sectors = result

    assert offset > 0
    assert sectors > 0

def test_chunk_location_empty_data() -> None:
    # Create region with valid header but no chunk data
    minimal_data = bytearray(8192) # 8KB of zeros (valid but empty header)
    region = Region(bytes(minimal_data))

    result = region.chunk_location(0, 0)
    assert result == (0, 0)

def test_chunk_location_raises_error() -> None:
    with pytest.raises(EmptyRegionFile):
        region = Region(b'')
        region.chunk_location(0, 0)
