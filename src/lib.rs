use pyo3::prelude::*;

// Import our modules
mod block;
mod chunk;
mod errors;
mod nbt;
mod region;

// Re-export for Python
pub use block::*;
pub use chunk::*;
pub use errors::*;
pub use nbt::*;
pub use region::*;

/// A Python module implemented in Rust.
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Add classes
    m.add_class::<RustRegion>()?;
    m.add_class::<RustChunk>()?;
    m.add_class::<StreamBlocksIterator>()?;
    m.add_class::<RustBlock>()?;
    m.add_class::<RustOldBlock>()?;
    m.add_class::<PyNbtFile>()?;
    m.add_class::<PyNbtCompound>()?;
    m.add_class::<PyNbtValue>()?;

    // Add custom exceptions
    m.add(
        "InvalidFileType",
        m.py().get_type_bound::<errors::InvalidFileType>(),
    )?;
    m.add(
        "EmptyRegionFile",
        m.py().get_type_bound::<errors::EmptyRegionFile>(),
    )?;
    m.add(
        "ChunkNotFound",
        m.py().get_type_bound::<errors::ChunkNotFound>(),
    )?;
    m.add(
        "OutOfBoundsCoordinates",
        m.py().get_type_bound::<errors::OutOfBoundsCoordinates>(),
    )?;
    m.add(
        "GZipChunkData",
        m.py().get_type_bound::<errors::GZipChunkData>(),
    )?;
    m.add(
        "CorruptedData",
        m.py().get_type_bound::<errors::CorruptedData>(),
    )?;

    // Add version info
    m.add("__version__", "0.1.0")?;

    Ok(())
}
