# anvil-parser

[![Documentation Status](https://readthedocs.org/projects/anvil-parser/badge/?version=latest)](https://anvil-parser.readthedocs.io/en/latest/?badge=latest)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/anvil-parser)](https://pypi.org/project/anvil-parser/)

A Python library for parsing [Minecraft anvil file format](https://minecraft.wiki/w/Anvil_file_format) with **experimental Rust acceleration** in development.

## Rust Backend Status - **WORK IN PROGRESS**

**Warning: Rust backend is under development and not functional yet.** This branch is building a pure Rust core with 100% API compatibility - all existing code will work unchanged, just faster.

**Current Status:**
- **Complete:** Rust project structure and Python bindings framework
- **In Progress:** Rust implementation incomplete - currently uses Python backend
- **Goal:** Pure Rust core with identical Python API

```
Current: Python backend only
Target: Rust core + Python API compatibility
```

# Installation

```bash
# Stable (Python-only)
pip install anvil-parser-modern

# Development (experimental Rust branch)
git clone https://github.com/voidfemme/anvil-parser.git
cd anvil-parser && git checkout experimental/rust-core
pip install -e .

# Rust development (structure exists, implementation incomplete)
pip install maturin && maturin develop
```

# Usage

API designed for automatic backend selection - currently Python-only, future Rust acceleration transparent:

```python
import anvil

# Load region and get blocks (works now, will be faster with Rust)
region = anvil.Region.from_file('r.0.0.mca')
chunk = anvil.Chunk.from_region(region, 0, 0)
block = chunk.get_block(0, 64, 0)

print(f"Backend: {anvil.BACKEND}")  # Currently 'python', future 'rust'
print(block)  # <Block(minecraft:stone)>

# Stream processing
for block in chunk.stream_chunk():
    if block.id == 'diamond_ore':
        print("Found diamond!")

# Create new regions
region = anvil.EmptyRegion(0, 0)
stone = anvil.Block('minecraft', 'stone')
region.set_block(stone, 0, 64, 0)
region.save('new_region.mca')
```

# Performance (When Complete)

**Expected Rust improvements:**
- Region loading: 5-15x faster
- Block iteration: 10-50x faster  
- NBT parsing: 8-20x faster
- Memory usage: 50-80% reduction

```bash
# Future benchmarking
python benchmarks/rust_vs_python.py region.mca
```

# Requirements

- **Python 3.10+**
- **NBT >= 1.5.1, frozendict >= 2.3.0, typing_extensions >= 4.14.0**
- **Optional:** Rust toolchain + Maturin >= 1.0 (for development)

# Features

## This Branch (Experimental)
- **Pure Rust core** (in development - structure complete, implementation pending)
- **100% API compatibility** - existing code works unchanged  
- **Maximum performance** with zero breaking changes
- **Benchmarking framework** ready

## Stable Improvements (Working Now)
- **Modern type annotations** (`X | None` syntax)
- **Enhanced null safety** and bug fixes
- **Python 3.13 compatibility**
- **pathlib.Path support**
- **Improved error handling**

# Development

## Current Priorities
1. **Rust NBT parsing** (fastnbt integration)
2. **Region file I/O** operations  
3. **Block/chunk data structures**
4. **API compatibility verification**
5. **Python binding completion**

## Contributing
- **Python:** Follow existing style, add type hints, write tests
- **Rust:** Core implementation in `src/`, maintain API compatibility, update `_rust.pyi`
- **Philosophy:** Feature parity first, then performance optimization

## Testing
```bash
pytest tests/                    # Run tests
pytest tests/ -m benchmark      # Run benchmarks (when Rust complete)
```

# Roadmap

**Before 1.0.0:**
- [ ] **Complete Rust implementation** (NBT, regions, blocks, chunks)
- [ ] **100% feature parity** with Python version
- [ ] **Performance validation** (10x+ improvements)
- [ ] **Comprehensive compatibility testing**
- [ ] **Python backend deprecation** (after parity verification)
- [ ] **New features** (additive only): Minecraft 1.21.4/1.21.5, biomes support

# Compatibility

**Tested:** Minecraft 1.14.4, 1.15.2, 1.16+ | Python 3.10-3.13

**Compatibility Promise:** All existing functions will continue to work exactly as before. New features may be added, but nothing will be removed or changed.

# Maintainer

Actively maintained by [voidfemme](https://github.com/voidfemme).

**Original:** [matcool/anvil-parser](https://github.com/matcool/anvil-parser) (archived)  
**Forked from:** [lexi-the-cute/anvil-parser](https://github.com/lexi-the-cute/anvil-parser)

---

> **Warning - Experimental Branch:** This rust-core branch targets maximum performance with full backward compatibility. All existing code will work unchanged, just faster. For production use, stick with the main branch until Rust migration is complete.
