from anvil.empty_chunk import EmptyChunk
from anvil.empty_region import EmptyRegion
from anvil.region import Region

from pathlib import Path

# DO NOT commit your generated .mca files. They should be excluded by gitignore,
# but double-check your unstaged/committed files before pushing.

SCRIPT_DATA_DIR = Path(__file__).parent / "data"

# Save your Minecraft-generated file from /file/to/minecraft/world/region/r0.0.mca
# and copy it to scripts/data/test_1_15_2_r0.0.mca
def compare_nbt_data_1_15_2() -> None:
    """Compare programmatic vs real 1.15.2 chunk NBT structure"""
    # Create data programmatically
    region = EmptyRegion(0, 0)
    empty_chunk = EmptyChunk(0, 0)
    region.add_chunk(empty_chunk)
    nbt = Region(region.save()).chunk_data(0, 0)
    
    # Real 1.15.2 chunk
    real_region = Region.from_file(SCRIPT_DATA_DIR / "test_1_15_2_r0.0.mca")
    real_nbt = real_region.chunk_data(0, 0)
    
    if nbt and real_nbt:
        print("\n=== 1.15.2 NBT Structure Comparison ===")
        print(f"Programmatic keys: {sorted(nbt.keys())}")
        print(f"Real keys: {sorted(real_nbt.keys())}")

        if 'Level' in real_nbt:
            print("Uses pre-1.18 'Level' structure")
            level_keys = sorted(real_nbt['Level'].keys())
            print(f"Level keys: {level_keys}")
        else:
            print("Missing 'Level' - might be a 1.18+ format")

        # Check for differences
        prog_keys = set(nbt.keys())
        real_keys = set(real_nbt.keys())

        if prog_keys != real_keys:
            print(f"Messing in programmatic: {real_keys - prog_keys}")
            print(f"Extra in programmatic: {prog_keys - real_keys}")
        else:
            print("Key structures match!")

def run_all_comparisons() -> None:
    versions = [compare_nbt_data_1_15_2]

    for compare_func in versions:
        try:
            compare_func()
        except FileNotFoundError as e:
            print(f"Skipping {compare_func.__name__}: {e}")
