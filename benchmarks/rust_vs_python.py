"""
Benchmark script to compare Rust vs Python implementation performance.
"""
import time
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import anvil
sys.path.insert(0, str(Path(__file__).parent.parent))

import anvil

def benchmark_region_loading(file_path: str, iterations: int = 10):
    """Benchmark region file loading."""
    print(f"Benchmarking region loading with {iterations} iterations...")
    
    # Check which backend is being used
    backend = "Rust" if hasattr(anvil, 'RUST_AVAILABLE') and anvil.RUST_AVAILABLE else "Python"
    print(f"Using {backend} backend")
    
    times = []
    for i in range(iterations):
        start_time = time.perf_counter()
        
        # Load the region file
        region = anvil.Region.from_file(file_path)
        
        # Do some basic operations
        chunk = region.get_chunk(0, 0)
        if chunk:
            block = chunk.get_block(0, 0, 0)
        
        end_time = time.perf_counter()
        times.append(end_time - start_time)
        print(f"  Iteration {i+1}: {times[-1]:.4f}s")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\nResults ({backend} backend):")
    print(f"  Average: {avg_time:.4f}s")
    print(f"  Min:     {min_time:.4f}s")
    print(f"  Max:     {max_time:.4f}s")
    
    return {
        'backend': backend,
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'times': times
    }

if __name__ == "__main__":
    # Use the test file from scripts/data
    test_file = Path(__file__).parent.parent / "scripts" / "data" / "test_1_15_2_r.0.0.mca"
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        print("Please ensure the test file exists or provide a path to an anvil region file.")
        sys.exit(1)
    
    results = benchmark_region_loading(str(test_file))
    
    # Save results for comparison
    import json
    results_file = Path(__file__).parent / f"benchmark_results_{results['backend'].lower()}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
