# C++ Backend

This directory contains the native compression core used by Python through `pybind11`.

## Features implemented
- Engine A: LZ-style coder (fast)
- Engine B: RLE-oriented coder
- Engine C: deeper-window LZ-style coder
- Reversible executable-aware normalization transforms for PE/ELF-like binaries

## Build (standalone)

```bash
cmake -S cpp -B cpp/build
cmake --build cpp/build -j
```

The `pamm_native` Python module is built through `pip install -e .` using `setup.py`.

## Benchmark
Use the end-to-end benchmark harness from repository root:

```bash
python benchmarks/benchmark.py /path/to/corpus
```
