use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

#[pyclass(name = "RustBlock")]
#[derive(Clone, Debug)]
pub struct RustBlock {
    #[pyo3(get)]
    pub namespace: String,
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub properties: HashMap<String, String>,
}

#[pymethods]
impl RustBlock {
    #[new]
    #[pyo3(signature = (namespace, block_id=None, *, properties=None))]
    pub fn new(
        namespace: String,
        block_id: Option<String>,
        properties: Option<HashMap<String, String>>,
    ) -> Self {
        let (final_namespace, final_id) = if let Some(block_id) = block_id {
            (namespace, block_id)
        } else {
            // If no block_id is given, assume namespace is actually the block_id
            ("minecraft".to_string(), namespace)
        };

        Self {
            namespace: final_namespace,
            id: final_id,
            properties: properties.unwrap_or_default(),
        }
    }

    /// Returns the block in the "minecraft:block_id" format
    pub fn name(&self) -> String {
        format!("{}:{}", self.namespace, self.id)
    }

    /// String representation like "Block(minecraft:stone)"
    pub fn __repr__(&self) -> String {
        format!("Block({})", self.name())
    }

    pub fn __str__(&self) -> String {
        self.__repr__()
    }

    /// Equality comparison
    pub fn __eq__(&self, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        // Try to extract as RustBlock
        if let Ok(other_block) = other.extract::<RustBlock>() {
            return Ok(self.namespace == other_block.namespace
                && self.id == other_block.id
                && self.properties == other_block.properties);
        }

        // Not a RustBlock, so not equal
        Ok(false)
    }

    /// Hash implementation
    pub fn __hash__(&self) -> u64 {
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        self.name().hash(&mut hasher);

        // Hash properties in a deterministic way
        let mut props: Vec<_> = self.properties.iter().collect();
        props.sort_by_key(|(k, _)| *k);
        for (k, v) in props {
            k.hash(&mut hasher);
            v.hash(&mut hasher);
        }

        hasher.finish()
    }

    /// Creates a new Block from the format: "namespace:block_id"
    #[classmethod]
    #[pyo3(signature = (name, *, properties=None))]
    pub fn from_name(
        _cls: &Bound<'_, PyType>,
        name: String,
        properties: Option<HashMap<String, String>>,
    ) -> PyResult<Self> {
        let parts: Vec<&str> = name.split(':').collect();
        if parts.len() != 2 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Name must be in format 'namespace:block_id'",
            ));
        }

        Ok(Self::new(
            parts[0].to_string(),
            Some(parts[1].to_string()),
            properties,
        ))
    }

    /// Creates a new Block from NBT palette format
    #[classmethod]
    pub fn from_palette(_cls: &Bound<'_, PyType>, tag: &Bound<'_, PyDict>) -> PyResult<Self> {
        // Get the 'Name' field
        let name_obj = tag
            .get_item("Name")?
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'Name' field"))?;

        // Extract the actual string value (assuming it has a .value attribute like NBT)
        let name: String = if let Ok(name_str) = name_obj.downcast::<pyo3::types::PyString>() {
            name_str.to_string()
        } else {
            // Try to get .value attribute for NBT compatibility
            let value_attr = name_obj.getattr("value")?;
            value_attr.extract()?
        };

        // Get properties if they exist
        let properties = if let Some(props_obj) = tag.get_item("Properties")? {
            Some(props_obj.extract::<HashMap<String, String>>()?)
        } else {
            None
        };

        Self::from_name(_cls, name, properties)
    }

    /// Creates a new Block from pre-flattening numeric ID (requires legacy map)
    #[classmethod]
    #[pyo3(signature = (block_id, *, data=0))]
    pub fn from_numeric_id(_cls: &Bound<'_, PyType>, block_id: u32, data: u32) -> PyResult<Self> {
        let key = format!("{}:{}", block_id, data);

        // For now, we'll return an error since we need to load the legacy map
        // In a real implementation, you'd load LEGACY_ID_MAP here
        Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
            format!("Legacy block conversion not yet implemented for {}", key),
        ))
    }
}

#[pyclass(name = "RustOldBlock")]
#[derive(Clone, Debug)]
pub struct RustOldBlock {
    #[pyo3(get)]
    pub id: u32,
    #[pyo3(get)]
    pub data: u32,
}

#[pymethods]
impl RustOldBlock {
    #[new]
    #[pyo3(signature = (block_id, data=0))]
    pub fn new(block_id: u32, data: u32) -> Self {
        Self { id: block_id, data }
    }

    /// Convert to modern Block format
    pub fn convert(&self) -> PyResult<RustBlock> {
        Python::with_gil(|py| {
            let cls = PyType::new_bound::<RustBlock>(py);
            RustBlock::from_numeric_id(&cls, self.id, self.data)
        })
    }

    pub fn __repr__(&self) -> String {
        format!("OldBlock(id={}, data={})", self.id, self.data)
    }

    pub fn __str__(&self) -> String {
        self.__repr__()
    }

    /// Equality comparison
    pub fn __eq__(&self, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        // Check if comparing with an integer
        if let Ok(other_int) = other.extract::<u32>() {
            return Ok(self.id == other_int);
        }

        // Check if comparing with another OldBlock
        if let Ok(other_block) = other.extract::<RustOldBlock>() {
            return Ok(self.id == other_block.id && self.data == other_block.data);
        }

        Ok(false)
    }

    /// Hash implementation
    pub fn __hash__(&self) -> u64 {
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        self.id.hash(&mut hasher);
        self.data.hash(&mut hasher);
        hasher.finish()
    }
}
