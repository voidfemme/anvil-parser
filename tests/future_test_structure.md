# Structure for minecraft versions
```
tests/
├── test_data/
│   ├── v1_14/
│   │   ├── level.dat
│   │   └── r.0.0.mca
│   ├── v1_15/
│   │   └── r.0.0.mca
│   ├── v1_18/  # Major change: new world height
│   │   └── r.0.0.mca
│   ├── v1_20/  # Current-ish
│   │   └── r.0.0.mca
│   └── README.md  # Document what changed between versions
├── test_version_compatibility.py  # Cross-version tests
└── test_*.py  # Your existing tests
```

**Major format changes to test:**
- 1.13 - "Flattening" - Block ID system overhaul
- 1.16 - "Nether height changes"
- 1.18 - World height expansion (-64 to 320)
- 1.20+ - Various NBT structure tweaks

## Testing strategy
```python
@pytest.mark.parameterize("version", ["v1_14", "v1_15", "v1_18", "v1_20"])
def test_chunk_data_across_versions(version):
    # Test some functionality across all versions
    pass

def test_v1_18_specific_height_limits():
    # Test version-specific features
    pass
```
