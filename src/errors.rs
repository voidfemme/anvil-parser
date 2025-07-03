use pyo3::exceptions::PyException;
use pyo3::prelude::*;

// Create custom Python exception types
pyo3::create_exception!(anvil_errors, InvalidFileType, PyException);
pyo3::create_exception!(anvil_errors, EmptyRegionFile, PyException);
pyo3::create_exception!(anvil_errors, ChunkNotFound, PyException);
pyo3::create_exception!(anvil_errors, OutOfBoundsCoordinates, PyException);
pyo3::create_exception!(anvil_errors, GZipChunkData, PyException);
pyo3::create_exception!(anvil_errors, CorruptedData, PyException);
pyo3::create_exception!(anvil_errors, InvalidChunkData, PyException);

#[derive(Debug, thiserror::Error)]
pub enum AnvilError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Invalid region file format")]
    InvalidFormat,

    #[error("Chunk not found at coordinates ({x}, {z})")]
    ChunkNotFound { x: i32, z: i32 },

    #[error("Invalid chunk data")]
    InvalidChunkData,

    #[error("Block coordinates ({x}, {y}, {z}) out of bounds")]
    OutOfBoundsCoordinates { x: i32, y: i32, z: i32 },

    #[error("Empty region file")]
    EmptyRegionFile,

    #[error("Expected str, Path, or file-like object, got {type_name}")]
    InvalidFileType { type_name: String },

    #[error("GZip compression not supported")]
    GZipChunkData,

    #[error("Corrupted data: {message}")]
    CorruptedData { message: String },
}

impl From<AnvilError> for PyErr {
    fn from(err: AnvilError) -> PyErr {
        match err {
            AnvilError::InvalidFileType { type_name } => {
                // Create custom InvalidFileType exceptions
                let err_msg = format!("Expected str, Path, or file-like object, got {type_name}");
                InvalidFileType::new_err(err_msg)
            }
            AnvilError::EmptyRegionFile => {
                // This should map to anvil.errors.EmptyRegionFile in Python
                EmptyRegionFile::new_err(err.to_string())
            }
            AnvilError::ChunkNotFound { x, z } => {
                ChunkNotFound::new_err(format!("Chunk not found at coordinates ({}, {})", x, z))
            }
            AnvilError::InvalidChunkData => InvalidChunkData::new_err(err.to_string()),
            AnvilError::OutOfBoundsCoordinates { x, y, z } => OutOfBoundsCoordinates::new_err(
                format!("Block coordinates ({}, {}, {}) out of bounds", x, y, z,),
            ),
            AnvilError::GZipChunkData => GZipChunkData::new_err(err.to_string()),
            AnvilError::CorruptedData { message } => CorruptedData::new_err(message),
            _ => PyException::new_err(err.to_string()),
        }
    }
}

pub type Result<T> = std::result::Result<T, AnvilError>;
