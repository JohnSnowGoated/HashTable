# HashTable

An open-addressing hash table in C that resolves collisions with **double hashing**, plus two visualizers that show, step by step, how keys are hashed, probed, inserted, searched and deleted.

The project has three parts:

| Part | File(s) | What it is |
|------|---------|------------|
| Console hash table | `hash_table.c` | Menu-driven string key/value hash table |
| Windows GUI visualizer | `hash_visualizer.c` | Native Win32 app that visualizes double hashing for integer keys |
| Python visualizer | `hash_visualizer.py` | Cross-platform Tkinter teaching tool for text keys, with step-by-step walkthrough |

---

## How it works

- **Table size:** fixed at 53 buckets (a prime).
- **Hash functions:** two polynomial hashes of the key, using bases `151` and `163`, each taken modulo the table size.
- **Probe sequence (double hashing):**

  ```
  index(attempt) = (hash_a + attempt * (hash_b + 1)) % table_size
  ```

  `attempt` starts at 0 and increases on every collision, so two keys that start in the same slot follow different probe paths. The `+ 1` guarantees the step is never zero.
- **Deletion with tombstones:** deleting a key does not empty its slot; it marks it with a *tombstone* (a sentinel item). This keeps later probe sequences intact, so keys stored after a collision can still be found.
- **Insert** reuses the first empty or tombstone slot, and **updates in place** if the key already exists.
- **Search / delete** follow the probe sequence until they find the key or hit an empty slot.

---

## Project structure

```
.
├── Makefile              # builds the GUI and console targets
├── hash_table.c          # console app: hash table + menu (self-contained)
├── hash_table.h          # header declaring the hash table API
├── prime.c / prime.h     # is_prime() / next_prime() helpers
├── hash_visualizer.c     # Win32 GUI visualizer
└── hash_visualizer.py    # Tkinter visualizer
```

> `hash_table.c` is self-contained (it defines its own types and `main`). `hash_table.h` and `prime.c/.h` are not used by the current Makefile; they are groundwork for resizing the table to the next prime.

---

## Building and running

### Requirements

- `gcc` (MinGW-w64 on Windows) and `make`
- Python 3 with Tkinter (for the Python visualizer; included with standard Python installers)

### Console version

```bash
make console
./hash_table.exe        # on Linux/macOS the output name is still hash_table.exe
```

Or compile directly:

```bash
gcc -std=gnu11 -Wall -Wextra -O2 -o hash_table hash_table.c -lm
./hash_table
```

Menu options:

```
1. Insert / Update Pair
2. Search Value by Key
3. Delete Key
4. Display Active Items
5. Exit
```

Keys and values are single words (up to 255 characters, no spaces).

### Windows GUI visualizer (C / Win32)

Windows only, since it uses the Win32 API.

```bash
make            # builds hash_visualizer.exe (default target)
make run        # build and launch
```

Type an integer into the input box and use **Insert**, **Search**, **Delete** or **Clear table**. The 53-slot grid highlights the probe path, and a trace panel shows the hash calculations and each probe attempt.

### Python visualizer (Tkinter)

Works on Windows, macOS and Linux:

```bash
python hash_visualizer.py
```

- Enter a **Key** and **Value**, then use **Insert / update**, **Search** or **Delete**.
- Step through the walkthrough to see how hash A and hash B are computed, which slots are probed, where collisions happen and where tombstones are left.
- Click a slot to inspect it.
- **Demo** automatically finds two keys that collide and replays a collision, an update, a delete (tombstone) and a search.
- **Clear** resets the table.

---

## Makefile targets

| Target | Description |
|--------|-------------|
| `make` / `make gui` | Build `hash_visualizer.exe` |
| `make console` | Build `hash_table.exe` |
| `make run` | Build and run the GUI |
| `make run-console` | Build and run the console app |
| `make clean` | Remove built executables |

Override the compiler or flags if needed, e.g. `make CC=clang CFLAGS="-O2"`.

---

## API (`hash_table.h`)

```c
ht_hash_table* ht_new(void);
void  ht_del_hash_table(ht_hash_table* ht);
void  ht_insert(ht_hash_table* ht, const char* key, const char* value);
char* ht_search(ht_hash_table* ht, const char* key);
void  ht_delete(ht_hash_table* ht, const char* key);
```

---

## Limitations

- The table has a fixed size of 53 and does not resize, so inserting into a full table is not handled.
- Keys and values are single tokens (no spaces) in the console app.
- The GUI visualizer accepts integer keys only; use the Python visualizer for text.
- The GUI visualizer is Windows-only.

## Possible improvements

- Resize and rehash when the load factor gets high, using `next_prime()` from `prime.c`.
- Reuse `hash_table.h` so the console app and library are separated.
- Add unit tests for insert, update, delete and tombstone reuse.

## Repository

<https://github.com/JohnSnowGoated/HashTable>
