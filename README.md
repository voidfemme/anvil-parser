# anvil-parser
<!--[![CodeFactor](https://www.codefactor.io/repository/github/voidfemme/anvil-parser/badge/master)](https://www.codefactor.io/repository/github/voidfemme/anvil-parser/overview/master)-->
[![Documentation Status](https://readthedocs.org/projects/anvil-parser/badge/?version=latest)](https://anvil-parser.readthedocs.io/en/latest/?badge=latest)
<!--[![Tests](https://github.com/voidfemme/anvil-parser/actions/workflows/run-pytest.yml/badge.svg)](https://github.com/voidfemme/anvil-parser/actions/workflows/run-pytest.yml)-->
[![PyPI - Downloads](https://img.shields.io/pypi/dm/anvil-parser)](https://pypi.org/project/anvil-parser/)

Simple parser for the [Minecraft anvil file format](https://minecraft.gamepedia.com/Anvil_file_format)

# Installation
This is a fork of the original anvil-parser with modern type annotations and improvements.

Install from PyPI:
```bash
pip install anvil-parser-modern
```

Install directly from this GitHub repository:
```bash
# Users
pip install git+https://github.com/voidfemme/anvil-parser.git

# Contributors
pip install -r requirements-dev.txt
pip install -e .
```

Or clone and install locally:
```bash
git clone https://github.com/voidfemme/anvil-parser.git
cd anvil-parser
pip install -e
```

# Usage
## Reading
```python
import anvil

region = anvil.Region.from_file('r.0.0.mca')

# You can also provide the region file name instead of the object
chunk = anvil.Chunk.from_region(region, 0, 0)

# If `section` is not provided, will get it from the y coords
# and assume it's global
block = chunk.get_block(0, 0, 0)

print(block) # <Block(minecraft:air)>
print(block.id) # air
print(block.properties) # {}
```

## Making own regions
```python
import anvil
from random import choice

# Create a new region with the `EmptyRegion` class at 0, 0 (in region coords)
region = anvil.EmptyRegion(0, 0)

# Create `Block` objects that are used to set blocks
stone = anvil.Block('minecraft', 'stone')
dirt = anvil.Block('minecraft', 'dirt')

# Make a 16x16x16 cube of either stone or dirt blocks
for y in range(16):
    for z in range(16):
        for x in range(16):
            region.set_block(choice((stone, dirt)), x, y, z)

# Save to a file
region.save('r.0.0.mca')
```

# Requirements
- Python 3.10+ (for modern type annotation syntax)
- NBT >= 1.5.1
- frozendict >= 2.3.0

# Changes from Original
This fork includes the following improvements:
- Modern Python type annotations using 'X | None' syntax
- Enhanced null safety throughout the codebase
- Bug fixes in block comparison methods
- Improved code organization with base classes
- Python 3.13 compatibility
- Updated dependencies
- **pathlib.Path support** for modern file handling

# Todo
*things to do before 1.0.0*
- [x] Proper documentation
- [ ] Add support for Minecraft version 1.21.4 and 1.21.5
- [ ] Biomes
- [x] CI
- [ ] More tests
  - [ ] Tests for 20w17a+ BlockStates format

# Note
Testing done in 1.14.4 and 1.15.2, more versions to be supported soon!

# Maintainer
This fork is actively maintained by [voidfemme](https://github.com/voidfemme).

**Original project:** [matcool/anvil-parser](https://github.com/matcool/anvil-parser) (archived)
**Forked from:** [lexi-the-cute/anvil-parser](https://github.com/lexi-the-cute/anvil-parser)
