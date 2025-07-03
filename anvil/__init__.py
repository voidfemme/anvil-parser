"""
anvil-parser: A Python library for reading and writing Minecraft Anvil files.

This version includes optional Rust acceleration for better performance.
"""

# Version info
__version__ = "0.10.0"

# Try Rust backend first, fall back to Python
try:
    from ._rust import (
        RustBlock as Block,
        RustOldBlock as OldBlock,
        RustChunk as Chunk,
        RustRegion as Region,
        __version__ as _rust_version
    )
    BACKEND = 'rust'
    RUST_AVAILABLE = True
    print(f"🚀 Using Rust backend (v{_rust_version}) for optimal performance")
    
except ImportError:
    from .block import Block, OldBlock
    from .chunk import Chunk
    from .region import Region
    BACKEND = 'python'
    RUST_AVAILABLE = False
    print("🐍 Using Python backend")

# Always expose Python implementations for advanced users and testing
from typing import Callable, Any
from .block import Block as PythonBlock, OldBlock as PythonOldBlock
from .chunk import Chunk as PythonChunk
from .region import Region as PythonRegion

# Import other necessary modules
from .empty_region import EmptyRegion
from .empty_chunk import EmptyChunk
from .base_section import BaseSection
from .empty_section import EmptySection
from .raw_section import RawSection
from .utils import _update_fmt, bin_append
from .errors import *

# Expose useful constants from chunk module
from .chunk import (
    _VERSION_21w43a,
    _VERSION_21w39a, 
    _VERSION_21w15a,
    _VERSION_21w06a,
    _VERSION_20w45a,
    _VERSION_20w17a,
    _VERSION_19w11a,
    _VERSION_17w47a
)

# Expose Rust classes if available (for type hints, advanced usage)
if RUST_AVAILABLE:
    # Create wrapper functions that convert Rust exceptions to proper Python ones
    from . import errors as anvil_errors
    from ._rust import (
        RustBlock, RustOldBlock, RustChunk, RustRegion
    )

    def _wrap_rust_region_from_file(original_from_file) -> Callable[..., Any]:
        """Wraps RustRegion.from_file to convert TypeError to InvalidFileType"""
        @classmethod
        def from_file(cls, file):
            try:
                return original_from_file(file)
            except TypeError as e:
                if "Expected str or file-like object" in str(e):
                    raise anvil_errors.InvalidFileType(str(e))
                raise
        return from_file

    def _wrap_rust_region_chunk_location(original_chunk_location) -> Callable[..., Any]:
        """Wraps RustRegion.chunk_location to convert RuntimeError to EmptyRegionFile"""
        def chunk_location(self, x: int, z: int):
            try:
                return original_chunk_location(self, x, z)
            except RuntimeError as e:
                if "Empty region file" in str(e):
                    raise anvil_errors.EmptyRegionFile(str(e))
                raise
        return chunk_location

    def _wrap_rust_region_get_chunk(original_get_chunk) -> Callable[..., Any]:
        """Wraps RustRegion.get_chunk to convert RuntimeError to EmptyRegionFile"""
        def get_chunk(self, x: int, z: int):
            try:
                return original_get_chunk(self, x, z)
            except RuntimeError as e:
                if "Empty Region file" in str(e):
                    raise anvil_errors.EmptyRegionFile(str(e))
                raise
        return get_chunk

    # Apply the wrappers
    RustRegion.from_file = _wrap_rust_region_from_file(RustRegion.from_file)
    RustRegion.chunk_location = _wrap_rust_region_chunk_location(RustRegion.chunk_location)
    RustRegion.get_chunk = _wrap_rust_region_get_chunk(RustRegion.get_chunk)
else:
    RustBlock = RustOldBlock = RustChunk = RustRegion = None

__all__ = [
    # Main API - uses best backend automatically
    'Block', 'OldBlock', 'Chunk', 'Region',
    
    # Backend info
    'BACKEND', 'RUST_AVAILABLE', '__version__',
    
    # Other classes
    'EmptyRegion', 'EmptyChunk', 'BaseSection', 'EmptySection', 'RawSection',
    
    # Utilities
    '_update_fmt', 'bin_append',
    
    # Version constants
    '_VERSION_21w43a', '_VERSION_21w39a', '_VERSION_21w15a',
    '_VERSION_21w06a', '_VERSION_20w45a', '_VERSION_20w17a', 
    '_VERSION_19w11a', '_VERSION_17w47a',
    
    # Explicit backends for advanced users
    'PythonBlock', 'PythonOldBlock', 'PythonChunk', 'PythonRegion',
    'RustBlock', 'RustOldBlock', 'RustChunk', 'RustRegion',
]
