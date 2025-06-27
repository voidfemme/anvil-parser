import context as _
from anvil import Region
import io
import secrets

# TODO: Implement tests for anvil/region.py
#
# TestRegion class:
#   - A test for chunk_location() to ensure it returns the correct offset and sector count for a given chunk.
#   - A test for chunk_location() on a non-existent chunk to ensure it returns `(0, 0)`.
#   - A test for chunk_data() on a non-existent chunk to ensure it returns `None`.

def test_from_filename(tmp_path):
    filename = tmp_path / "region.mca"
    contents = secrets.token_bytes()

    with open(filename, 'wb') as f:
        f.write(contents)

    region = Region.from_file(str(filename))
    assert region.data == contents

def test_from_filelike():
    contents = secrets.token_bytes()
    filelike = io.BytesIO(contents)

    region = Region.from_file(filelike)
    assert region.data == contents
