# Code Reflection Parallelization Summary

## Parallelization Implementation

The `run_code_reflection.py` script has been modified to support parallel processing while maintaining compatibility with the original sequential behavior.

### Key Changes

1. **Added `--num-workers` argument**: Specifies the number of parallel worker processes (default: 1 for backward compatibility)

2. **Two execution modes**:
   - `--num-workers 1`: Sequential processing (original behavior)
   - `--num-workers N` (N > 1): Parallel processing using multiprocessing.Pool

3. **Thread-safe file operations**: Added file locking mechanism to prevent race conditions when multiple processes write to the results file

## Output Ordering Analysis

### ✅ **Ordering is NOT critical** - Here's why:

1. **Results structure**: The output is a **JSON dictionary**, not a list:
   ```json
   {
     "game1_v0.py": {"metrics": {...}, "reflection_prompt": "...", ...},
     "game2_v0.py": {"metrics": {...}, "reflection_prompt": "...", ...},
     ...
   }
   ```

2. **Downstream consumption**: Analysis scripts (`make_table2.py`, `make_table3.py`, etc.) access results by **filename keys**, not by position:
   ```python
   data = json.load(f)  # Load as dictionary
   for k, v in data.items():  # Iterate over key-value pairs
       result = data[game_reflection]  # Access by key, not index
   ```

3. **Key-based access**: No code depends on the insertion order of dictionary entries

### 🛡️ **Deterministic output preserved** - Additional safeguards:

1. **Sorted file processing**: Games are processed in alphabetical order even in parallel mode
2. **Ordered result collection**: Using `pool.imap()` instead of `pool.imap_unordered()` to maintain processing order
3. **Sorted JSON output**: Added `sort_keys=True` to ensure consistent JSON formatting

## Usage Examples

```bash
# Sequential processing (original behavior)
python scripts/run_code_reflection.py --game-folder data/programs --num-workers 1

# Parallel processing with 4 workers
python scripts/run_code_reflection.py --game-folder data/programs --num-workers 4

# Use all CPU cores
python scripts/run_code_reflection.py --game-folder data/programs --num-workers $(nproc)
```

## Safety Features

1. **File locking**: Prevents corruption when multiple processes write to results file
2. **Atomic writes**: Uses temporary files and atomic moves to prevent partial writes
3. **Error handling**: Graceful handling of file I/O errors and timeouts
4. **Backward compatibility**: `--num-workers 1` produces identical behavior to original code

## Performance Considerations

- **I/O bound tasks**: Parallel processing is most beneficial for I/O intensive operations (file reading, API calls)
- **Memory usage**: Each worker process has its own memory space
- **Optimal worker count**: Typically 2-4x number of CPU cores for I/O bound tasks, but may need tuning based on API rate limits

## Conclusion

The parallelization is **safe** because:
- Output structure is a dictionary (key-based access)
- Downstream consumers don't depend on insertion order
- Additional safeguards ensure deterministic output
- File operations are thread-safe
