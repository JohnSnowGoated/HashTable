# Hash Table in C (Open Addressing & Double Hashing)

A lightweight C implementation of a String Key-Value Hash Table using **open addressing** and **double hashing** for collision resolution.

## Features

- **Double Hashing**: Uses two polynomial rolling hash functions to calculate dynamic probe stride step sizes, preventing primary/secondary clustering.
- **Tombstone Deletion**: Safely handles deletion using sentinel tombstones (`HT_DELETED`) so existing search probe chains remain unbroken.
- **Prime Utilities**: Built-in prime number calculations (`is_prime`, `next_prime`) for table capacity sizing.
- **Interactive CLI**: Menu-driven terminal interface to insert, search, delete, and view table entries.

## File Structure

```text
├── hash_table.h   # Hash table struct definitions & prototypes
├── hash_table.c   # Core table allocation, double hashing, & operations
├── prime.h        # Prime utility function prototypes
├── prime.c        # Prime checking and next prime algorithms
├── main.c         # Interactive menu driver program
└── Makefile       # Build automation script
```

## Quick Start

### Interactive GUI

Launch the pop-out bucket visualizer with Python 3, Tkinter, and GCC installed:

```bash
python3 hash_table_gui.py
```

The window calls the C hash-table implementation directly. Insert, search, and delete operations show the two hash values, probe stride, bucket-by-bucket results, and the final bucket state. Use the playback controls to step through or animate an operation. The GUI builds its shared library in a temporary directory.

### Build & Run via Makefile

```bash
make run
```

### Manual Compilation

```bash
gcc main.c hash_table.c prime.c -o hashtable -lm
./hashtable
```
