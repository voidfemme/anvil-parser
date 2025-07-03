use crate::block::RustBlock;
use crate::nbt::PyNbtCompound;
use crate::{AnvilError, PyNbtFile, RustRegion};
use pyo3::prelude::*;
use pyo3::types::PyType;

const _VERSION_21W43A: i32 = 2844;
const _VERSION_21W39A: i32 = 2836;
const _VERSION_21W15A: i32 = 2709;
const _VERSION_21W06A: i32 = 2694;
const _VERSION_20W45A: i32 = 2681;
const _VERSION_20W17A: i32 = 2529;
const _VERSION_19W11A: i32 = 1937;
const _VERSION_17W47A: i32 = 1451;
// const _VERSION_12W07A: i32 = -1;

#[pyclass(name = "RustChunk")]
pub struct RustChunk {
    pub nbt_data: Option<PyNbtFile>,
    #[pyo3(get)]
    pub x: i32,
    #[pyo3(get)]
    pub z: i32,
    #[pyo3(get)]
    pub version: Option<i32>,
    #[pyo3(get)]
    pub lowest_y: Option<i32>,
    #[pyo3(get)]
    pub highest_y: Option<i32>,
    // Block entities (modern term)
    #[pyo3(get)]
    pub block_entities: Option<PyNbtCompound>,
    // Tile entities (legacy term, same as block_entities)
    #[pyo3(get)]
    pub tile_entities: Option<PyNbtCompound>,
    // Store the main data compound for easier access
    pub data: Option<PyNbtCompound>,
}

#[pyclass(name = "StreamBlocksIterator")]
pub struct StreamBlocksIterator {
    current_index: usize,
    max_index: usize,
    _section: Option<PyNbtCompound>,
    _palette: Vec<RustBlock>,
    _force_new: bool,
}

#[pymethods]
impl StreamBlocksIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self) -> PyResult<Option<RustBlock>> {
        if self.current_index >= self.max_index {
            return Ok(None);
        }

        // TODO: parse the actual block data from NBT
        // for now, return air blocks

        let block = Python::with_gil(|py| -> PyResult<RustBlock> {
            let rust_block_type = PyType::new_bound::<RustBlock>(py);
            RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
        })?;

        self.current_index += 1;
        Ok(Some(block))
    }
}

/// Creates a new chunk.
///
/// # Arguments
/// * `nbt_data` - Optional NBT data for the chunk
///
/// # Returns
/// A new `RustChunk` instance
#[pymethods]
impl RustChunk {
    #[new]
    pub fn new(nbt_data: PyNbtFile) -> PyResult<Self> {
        let mut chunk = Self {
            nbt_data: Some(nbt_data.clone()),
            x: 0,
            z: 0,
            version: None,
            lowest_y: Some(0),
            highest_y: Some(15),
            block_entities: None,
            tile_entities: None, // Will be set to same as block_entities
            data: None,
        };

        chunk.init_from_nbt(&nbt_data)?;

        Ok(chunk)
    }

    // Create an empty chunk (for testing purposes)
    #[classmethod]
    pub fn empty(_cls: &Bound<'_, PyType>) -> PyResult<Self> {
        Ok(Self {
            nbt_data: None,
            x: 0,
            z: 0,
            version: None,
            lowest_y: Some(0),
            highest_y: Some(15),
            block_entities: None,
            tile_entities: None,
            data: None,
        })
    }

    // Alternative constructor for cases where NBTFile is passed as positional arg
    #[pyo3(signature = (*args))]
    #[staticmethod]
    pub fn from_nbt_file(args: &Bound<'_, pyo3::types::PyTuple>) -> PyResult<Self> {
        let nbt_data = if !args.is_empty() {
            match args.get_item(0)?.extract::<PyNbtFile>() {
                Ok(nbt) => Some(nbt),
                Err(_) => None, // If extraction fails, treat as None
            }
        } else {
            None
        };

        let chunk = Self {
            nbt_data: nbt_data.clone(),
            x: 0,
            z: 0,
            version: None,
            lowest_y: Some(0),
            highest_y: Some(15),
            block_entities: None,
            tile_entities: None, // Wil be set to same as block_entities
            data: None,
        };

        Ok(chunk)
    }

    /// Alternative constructor for cases where NBTFile is passed as bytes (Vec<u8>)
    #[classmethod]
    #[pyo3(signature = (nbt_data=None))]
    fn from_nbt_data(_cls: &Bound<'_, PyType>, nbt_data: Option<PyNbtFile>) -> PyResult<Self> {
        let mut chunk = Self {
            nbt_data: nbt_data.clone(),
            x: 0,
            z: 0,
            version: None,
            lowest_y: Some(0),
            highest_y: Some(15),
            block_entities: None,
            tile_entities: None,
            data: None,
        };

        if let Some(ref nbt) = nbt_data {
            chunk.init_from_nbt(nbt)?;
        }
        Ok(chunk)
    }

    fn init_from_nbt(&mut self, nbt_data: &PyNbtFile) -> PyResult<()> {
        // Extract version
        self.version = nbt_data
            .get("DataVersion")
            .and_then(|v| Python::with_gil(|py| v.value().extract::<i32>(py).ok()));

        // #xtract main data compound
        if let Some(version) = self.version {
            // Modern format: data is at root level
            if version >= _VERSION_21W43A {
                self.data = Some(nbt_data.value.clone());
            } else {
                // Legacy format: data is under "Level"
                self.data = nbt_data.get("Level").and_then(|level| {
                    Python::with_gil(|py| level.value().extract::<PyNbtCompound>(py).ok())
                })
            }
        } else {
            // Pre-version chunk, assume legacy format
            self.data = nbt_data.get("Level").and_then(|level| {
                Python::with_gil(|py| level.value().extract::<PyNbtCompound>(py).ok())
            });
        };

        // Extract coordinates
        if let Some(ref data) = self.data {
            self.x = data
                .get("xPos")
                .and_then(|v| Python::with_gil(|py| v.value().extract::<i32>(py).ok()))
                .unwrap_or(0);
            self.z = data
                .get("zPos")
                .and_then(|v| Python::with_gil(|py| v.value().extract::<i32>(py).ok()))
                .unwrap_or(0);
        }

        // Calculate Y bounds
        self.lowest_y = self.get_lowest_section();
        self.highest_y = self.get_highest_section();

        self.init_block_entities()?;

        Ok(())
    }

    fn init_block_entities(&mut self) -> PyResult<()> {
        if let Some(ref data) = self.data {
            if let Some(version) = self.version {
                if version >= _VERSION_21W43A {
                    self.tile_entities = data.get("block_entities").and_then(|v| {
                        Python::with_gil(|py| v.value().extract::<PyNbtCompound>(py).ok())
                    });
                } else {
                    self.tile_entities = data.get("TileEntities").and_then(|v| {
                        Python::with_gil(|py| v.value().extract::<PyNbtCompound>(py).ok())
                    });
                }
            } else {
                self.tile_entities = data.get("TileEntities").and_then(|v| {
                    Python::with_gil(|py| v.value().extract::<PyNbtCompound>(py).ok())
                });
            }
        }

        // Match modern naming
        self.block_entities = self.tile_entities.clone();
        Ok(())
    }

    fn get_lowest_section(&mut self) -> Option<i32> {
        if let Some(ref data) = self.data {
            if let Some(version) = self.version {
                if version >= _VERSION_21W43A {
                    if let Some(_sections) = data.get("sections") {
                        // TODO: extract last section Y value
                        return Some(-69); // Placeholder
                    }
                } else {
                    if let Some(_sections) = data.get("Sections") {
                        // TODO: extract last section Y value
                        return Some(-6);
                    }
                }
            }
        }
        None
    }

    fn get_highest_section(&mut self) -> Option<i32> {
        if let Some(ref data) = self.data {
            if let Some(version) = self.version {
                if version >= _VERSION_21W43A {
                    if let Some(_sections) = data.get("sections") {
                        // TODO: extract last section Y value
                        return Some(69); // Placeholder
                    }
                } else {
                    if let Some(_sections) = data.get("Sections") {
                        // TODO: extract last section Y value
                        return Some(69);
                    }
                }
            }
        }
        None
    }

    /// Returns the section at given Y index
    pub fn get_section(&self, y: i32) -> PyResult<Option<PyNbtCompound>> {
        // Check bounds
        if let (Some(lowest), Some(highest)) = (self.lowest_y, self.highest_y) {
            if y < lowest || y > highest {
                return Err(AnvilError::OutOfBoundsCoordinates { x: 0, y, z: 0 }.into());
            }
        }

        if let Some(ref data) = self.data {
            let sections_key = if self.version.unwrap_or(0) >= _VERSION_21W43A {
                "sections"
            } else {
                "Sections"
            };

            if let Some(_sections) = data.get(sections_key) {
                // TODO: iterate through sections and find matching Y
                // This is a simplified placeholder
                return Ok(None);
            }
        }

        Ok(None)
    }

    /// Returns the block palette for given section
    pub fn get_palette(&self, _section: &Bound<'_, PyAny>) -> PyResult<Option<Vec<RustBlock>>> {
        // TODO: This would require parsing the NBT section data
        // Placeholder implementation
        let block = Python::with_gil(|py| -> PyResult<RustBlock> {
            let rust_block_type = PyType::new_bound::<RustBlock>(py);
            RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
        })?;

        Ok(Some(vec![block]))
    }

    /// Returns the block in the given coordinates
    ///
    /// # Arguments
    /// * `x` - Block's X coordinate in the chunk (0-15)
    /// * `y` - Block's Y coordinate (world height)
    /// * `z` - Block's Z coordinate in the chunk (0-15)
    /// * `section` - Either a section NBT tag or an index. If no section is given,
    /// assume Y is global and use it for getting the section
    ///
    /// # Returns
    /// The Block object at the given coordinates, or `None`
    ///
    /// # Raises
    /// * `OutOfBoundsCoordinates` - If X or Z are not in the range 0-15
    ///
    /// # Examples
    /// ```python
    /// chunk = RustChunk()
    /// block = chunk.get_block(8, 64, 8) # Get block at center of chunk
    /// ```
    #[pyo3(signature = (x, y, z, section=None, force_new=false))]
    pub fn get_block(
        &self,
        x: i32,
        y: i32,
        z: i32,
        section: Option<&Bound<'_, PyAny>>,
        force_new: Option<bool>,
    ) -> PyResult<Option<RustBlock>> {
        // Bounds checking
        let lowest_bound = self.lowest_y.map(|ly| ly * 16).unwrap_or(i32::MIN);
        let highest_bound = self.highest_y.map(|ly| ly * 16).unwrap_or(i32::MAX);

        if x < 0 || x > 15 {
            return Err(AnvilError::OutOfBoundsCoordinates { x, y, z }.into());
        }
        if z < 0 || z > 15 {
            return Err(AnvilError::OutOfBoundsCoordinates { x, y, z }.into());
        }
        if y < lowest_bound || y > highest_bound {
            return Err(AnvilError::OutOfBoundsCoordinates { x, y, z }.into());
        }

        let mut _section_y = y;
        let section_obj = match section {
            None => {
                _section_y = y % 16;
                self.get_section(y / 16)?
            }
            Some(section_bound) => {
                if let Ok(section_int) = section_bound.extract::<i32>() {
                    self.get_section(section_int)?
                } else {
                    // Assume it's an NBT compound
                    section_bound.extract::<PyNbtCompound>().ok()
                }
            }
        };

        // let block = Python::with_gil(|py| -> PyResult<RustBlock> {
        //     let rust_block_type = PyType::new_bound::<RustBlock>(py);
        //     RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
        // })?;

        // Handle pre-flattening vs modern format
        if self.version.is_none() || self.version.unwrap() < _VERSION_17W47A {
            // Pre-flattening format - would return OldBlock
            if section_obj.is_none() {
                if force_new.unwrap() {
                    let block = Python::with_gil(|py| -> PyResult<RustBlock> {
                        let rust_block_type = PyType::new_bound::<RustBlock>(py);
                        RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
                    })?;
                    return Ok(Some(block));
                } else {
                    // Would return RustOldBlock, but converting for now
                    // TODO: return RustOldBlock

                    let block = Python::with_gil(|py| -> PyResult<RustBlock> {
                        let rust_block_type = PyType::new_bound::<RustBlock>(py);
                        RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
                    })?;

                    return Ok(Some(block));
                }
            }
            // TODO: implement block ID extraction from NBT
        }

        // Modern format
        if section_obj.is_none() {
            let block = Python::with_gil(|py| -> PyResult<RustBlock> {
                let rust_block_type = PyType::new_bound::<RustBlock>(py);
                RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
            })?;
            return Ok(Some(block));
        }

        // This is where the complex block state parsing should happen
        // For now, return air as placeholder
        let block = Python::with_gil(|py| -> PyResult<RustBlock> {
            let rust_block_type = PyType::new_bound::<RustBlock>(py);
            RustBlock::from_name(&rust_block_type, "minecraft:air".to_string(), None)
        })?;
        Ok(Some(block))
    }

    pub fn set_block(&mut self, _x: i32, _y: i32, _z: i32, _block: RustBlock) -> PyResult<()> {
        // Placeholder implementation
        Ok(())
    }

    /// Returns a generator for all the blocks in given section
    #[pyo3(signature = (index=0, section=None, force_new=false))]
    pub fn stream_blocks(
        &self,
        index: Option<usize>,
        section: Option<&Bound<'_, PyAny>>,
        force_new: bool,
    ) -> PyResult<StreamBlocksIterator> {
        let section_obj = match section {
            Some(s) => {
                if let Ok(section_int) = s.extract::<i32>() {
                    if section_int < 0 || section_int > 16 {
                        return Err(AnvilError::OutOfBoundsCoordinates {
                            x: 0,
                            y: section_int,
                            z: 0,
                        }
                        .into());
                    }
                    self.get_section(section_int)?
                } else {
                    s.extract::<PyNbtCompound>().ok()
                }
            }
            None => self.get_section(0)?,
        };

        Ok(StreamBlocksIterator {
            current_index: index.unwrap(),
            max_index: 4096, // 16^3
            _section: section_obj,
            _palette: vec![], // TODO: populate from section data
            _force_new: force_new,
        })
    }

    #[pyo3(signature = (index=0))]
    pub fn stream_chunk(&self, index: usize) -> PyResult<StreamBlocksIterator> {
        // TODO: a helper that iterates through all sections.
        // for now, just delegate to stream_blocks for section 0
        self.stream_blocks(Some(index), None, false)
    }

    /// Get block entity at given coordinates
    pub fn get_block_entity(&self, _x: i32, _y: i32, _z: i32) -> Option<PyNbtCompound> {
        // TODO: iterate through self.block_entities and find matching coordinates
        // placeholder implemntation:
        None
    }

    /// Legacy alias for get_block_entity
    pub fn get_tile_entity(&self, x: i32, y: i32, z: i32) -> Option<PyNbtCompound> {
        self.get_block_entity(x, y, z)
    }

    /// Creates a new chunk from region and the chunk's X and Z
    ///
    /// # Parameters
    /// * `region` - The region with the chunk
    /// * `chunk_x` - The chunk's X coordinate
    /// * `chunk_z` - The chunk's Z coordinate
    ///
    /// # Returns
    /// The Class of the NBT data? The chunk?
    ///
    /// # Raises
    /// `ChunkNotFound` - if the nbt_data is None
    ///
    /// # Examples
    /// ```python
    /// region = RustRegion()
    /// chunk = region.from_region(region, 5, 8) # Get chunk at (5, 8) in the given region
    /// ```
    #[classmethod]
    #[pyo3(signature = (region, chunk_x, chunk_z))]
    pub fn from_region(
        _cls: &Bound<'_, PyType>,
        region: &Bound<'_, PyAny>,
        chunk_x: i32,
        chunk_z: i32,
    ) -> PyResult<Self> {
        // Handle different region types
        let actual_region = if let Ok(_region_str) = region.extract::<String>() {
            // Case 1: String file path - create region from file
            RustRegion::from_file(_cls, region)?
        } else if let Ok(region_obj) = region.extract::<RustRegion>() {
            // Case 2: Already a RustRegion object
            region_obj
        } else {
            // Case 3: Invalid type
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "region must be a string file or RustRegion object",
            ));
        };

        // Get chunk data from region
        let nbt_data = actual_region.chunk_data(chunk_x, chunk_z);

        // Check if the chunk exists
        let nbt_data = match nbt_data {
            None => {
                return Err(AnvilError::ChunkNotFound {
                    x: chunk_x,
                    z: chunk_z,
                }
                .into());
            }
            Some(data) => data,
        };

        // Convert bytes to NBTFile
        let nbt_file = if !nbt_data.is_empty() {
            Some(PyNbtFile::from_bytes(_cls, nbt_data)?)
        } else {
            None
        };

        // Create the chunk with NBT data
        let mut chunk = Python::with_gil(|py| {
            let cls = PyType::new_bound::<RustChunk>(py);
            RustChunk::from_nbt_data(&cls, nbt_file)
        })?;

        // Set chunk coordinates (extract from NBT if available)
        chunk.x = chunk_x;
        chunk.z = chunk_z;

        // Try to extract version from NBT data
        if let Some(ref nbt) = chunk.nbt_data {
            chunk.version = nbt
                .get("DataVersion")
                .and_then(|v| Python::with_gil(|py| v.value().extract::<i32>(py).ok()));
        }

        Ok(chunk)
    }
}
