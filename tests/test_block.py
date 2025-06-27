import context as _
from anvil import Block, OldBlock
from nbt import nbt

# TODO: Implement tests for anvil/block.py
#
# TestBlock class:
#   - A test to verify that Block.from_name() correctly parses a namespaced block ID.
#   - A test for Block.from_palette() to ensure it correctly creates a Block from an NBT tag.
#   - Tests for Block.from_numeric_id() to verify that it correctly converts legacy block IDs and data values to modern Block objects. Test with a variety of known legacy IDs.
#   - A test to ensure the __eq__ and __hash__ methods work as expected.
#
# TestOldBlock class:
#   - A test to verify that OldBlock.convert() correctly converts an OldBlock to a Block.
#   - A test for the __eq__ and __hash__ methods.
