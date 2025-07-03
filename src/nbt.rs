// NBT (Named Binary Tag) parsing utilities for Minecraft data
use pyo3::prelude::*;
use pyo3::types::PyType;
use std::collections::HashMap;

// Re-export fastnbt types for convenience
pub use fastnbt::Value as NbtValue;

/// Python-compatible NBT Tag types
#[pyclass(name = "NbtValue")]
#[derive(Clone, Debug)]
pub struct PyNbtValue {
    inner: NbtValueInner,
}

#[derive(Clone, Debug)]
enum NbtValueInner {
    Byte(i8),
    Short(i16),
    Int(i32),
    Long(i64),
    Float(f32),
    Double(f64),
    ByteArray(Vec<i8>),
    String(String),
    List(Vec<PyNbtValue>),
    Compound(HashMap<String, PyNbtValue>),
    IntArray(Vec<i32>),
    LongArray(Vec<i64>),
}

#[pyclass(name = "NbtCompound")]
#[derive(Clone, Debug)]
pub struct PyNbtCompound {
    #[pyo3(get)]
    pub data: HashMap<String, PyNbtValue>,
}

impl PyNbtValue {
    pub fn new_byte(value: i8) -> Self {
        Self {
            inner: NbtValueInner::Byte(value),
        }
    }

    pub fn new_string(value: String) -> Self {
        Self {
            inner: NbtValueInner::String(value),
        }
    }

    pub fn new_compound(value: HashMap<String, PyNbtValue>) -> Self {
        Self {
            inner: NbtValueInner::Compound(value),
        }
    }

    // Add other constructors as needed
}

#[pymethods]
impl PyNbtCompound {
    #[new]
    pub fn new() -> Self {
        Self {
            data: HashMap::new(),
        }
    }

    /// Get a value by key (like dict access)
    pub fn get(&self, key: &str) -> Option<PyNbtValue> {
        self.data.get(key).cloned()
    }

    /// Set a value by key
    pub fn set(&mut self, key: String, value: PyNbtValue) {
        self.data.insert(key, value);
    }

    /// Python dict-like access
    pub fn __getitem__(&self, key: &str) -> PyResult<PyNbtValue> {
        let key_owned = key.to_string();
        self.data
            .get(key)
            .cloned()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>(key_owned))
    }

    pub fn __setitem__(&mut self, key: String, value: PyNbtValue) {
        self.data.insert(key, value);
    }

    pub fn __contains__(&self, key: &str) -> bool {
        self.data.contains_key(key)
    }

    pub fn keys(&self) -> Vec<String> {
        self.data.keys().cloned().collect()
    }
}

#[pymethods]
impl PyNbtValue {
    /// Get the underlying value (similar to .value in Python NBT)
    #[getter]
    pub fn value(&self) -> PyObject {
        Python::with_gil(|py| match &self.inner {
            NbtValueInner::Byte(v) => v.to_object(py),
            NbtValueInner::Short(v) => v.to_object(py),
            NbtValueInner::Int(v) => v.to_object(py),
            NbtValueInner::Long(v) => v.to_object(py),
            NbtValueInner::Float(v) => v.to_object(py),
            NbtValueInner::Double(v) => v.to_object(py),
            NbtValueInner::String(v) => v.to_object(py),
            NbtValueInner::ByteArray(v) => v.to_object(py),
            NbtValueInner::IntArray(v) => v.to_object(py),
            NbtValueInner::LongArray(v) => v.to_object(py),
            NbtValueInner::List(v) => {
                // Convert Vec<PyNbtValue> to Python list
                let py_list: Vec<PyObject> = v.iter().map(|item| item.value()).collect();
                py_list.to_object(py)
            }
            NbtValueInner::Compound(v) => {
                // Convert HashMap<String, PyNbtValue> to Python dict
                let py_dict: HashMap<String, PyObject> =
                    v.iter().map(|(k, v)| (k.clone(), v.value())).collect();
                py_dict.to_object(py)
            }
        })
    }

    pub fn __repr__(&self) -> String {
        match &self.inner {
            NbtValueInner::String(s) => format!("NbtString('{}')", s),
            NbtValueInner::Int(i) => format!("NbtInt({})", i),
            NbtValueInner::Compound(_) => "NbtCompound({...})".to_string(),
            _ => format!("NbtValue({:?})", self.inner),
        }
    }
}

/// Convert fastnbt Value to our Python-compatible type
impl From<NbtValue> for PyNbtValue {
    fn from(value: NbtValue) -> Self {
        let inner = match value {
            NbtValue::Byte(v) => NbtValueInner::Byte(v),
            NbtValue::Short(v) => NbtValueInner::Short(v),
            NbtValue::Int(v) => NbtValueInner::Int(v),
            NbtValue::Long(v) => NbtValueInner::Long(v),
            NbtValue::Float(v) => NbtValueInner::Float(v),
            NbtValue::Double(v) => NbtValueInner::Double(v),
            NbtValue::String(v) => NbtValueInner::String(v),
            NbtValue::ByteArray(v) => NbtValueInner::ByteArray(v.to_vec()),
            NbtValue::IntArray(v) => NbtValueInner::IntArray(v.to_vec()),
            NbtValue::LongArray(v) => NbtValueInner::LongArray(v.to_vec()),
            NbtValue::List(v) => NbtValueInner::List(v.into_iter().map(|x| x.into()).collect()),
            NbtValue::Compound(v) => {
                NbtValueInner::Compound(v.into_iter().map(|(k, v)| (k, v.into())).collect())
            }
        };
        Self { inner }
    }
}

/// NBT File parser - equivalent to nbt.NBTFile
#[pyclass(name = "NbtFile")]
#[derive(Clone)]
pub struct PyNbtFile {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub value: PyNbtCompound,
}

#[pymethods]
impl PyNbtFile {
    #[new]
    pub fn new(name: String) -> Self {
        Self {
            name,
            value: PyNbtCompound::new(),
        }
    }

    /// Load NBT from file path
    #[classmethod]
    pub fn load(_cls: &Bound<'_, PyType>, filename: &str) -> PyResult<Self> {
        let data = std::fs::read(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

        Self::from_bytes(_cls, data)
    }

    /// Parse NBT from bytes
    #[classmethod]
    pub fn from_bytes(_cls: &Bound<'_, PyType>, data: Vec<u8>) -> PyResult<Self> {
        // Try to parse with fastnbt
        let parsed: HashMap<String, NbtValue> = fastnbt::from_bytes(&data)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        // Convert to our Python-compatible format
        let mut compound = PyNbtCompound::new();
        for (key, value) in parsed {
            compound.data.insert(key.clone(), value.into());
        }

        Ok(Self {
            name: "".to_string(), // fastnbt doesn't preserve root name
            value: compound,
        })
    }

    pub fn __getitem__(&self, key: &str) -> PyResult<PyNbtValue> {
        let key_owned = key.to_string();
        self.value
            .data
            .get(key)
            .cloned()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>(key_owned))
    }

    pub fn get(&self, key: &str) -> Option<PyNbtValue> {
        self.value.get(key)
    }
}
