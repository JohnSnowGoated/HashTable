import ctypes
import subprocess
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


ROOT = Path(__file__).resolve().parent
HT_KEY_MAX = 256
HT_TRACE_MAX_STEPS = 53

HT_SLOT_EMPTY = 0
HT_SLOT_OCCUPIED = 1
HT_SLOT_DELETED = 2

HT_TRACE_EMPTY = 0
HT_TRACE_COLLISION = 1
HT_TRACE_TOMBSTONE = 2
HT_TRACE_FOUND = 3
HT_TRACE_UPDATED = 4
HT_TRACE_DELETED = 5
HT_TRACE_MISS = 6

HT_RESULT_NOT_FOUND = 0
HT_RESULT_INSERTED = 1
HT_RESULT_UPDATED = 2
HT_RESULT_FULL = 3

COLORS = {
    "page": "#f1f4f2",
    "panel": "#ffffff",
    "ink": "#172622",
    "muted": "#64736e",
    "line": "#d8e1dc",
    "green": "#176b52",
    "green_light": "#e2f2e9",
    "blue_light": "#e5eff8",
    "amber": "#ffe0a6",
    "red_light": "#f8e4df",
    "empty": "#f7f9f8",
}


class TraceStep(ctypes.Structure):
    _fields_ = [
        ("index", ctypes.c_int),
        ("state", ctypes.c_int),
        ("action", ctypes.c_int),
        ("key", ctypes.c_char * HT_KEY_MAX),
        ("value", ctypes.c_char * HT_KEY_MAX),
    ]


class Trace(ctypes.Structure):
    _fields_ = [
        ("hash_a", ctypes.c_int),
        ("hash_b", ctypes.c_int),
        ("start_index", ctypes.c_int),
        ("stride", ctypes.c_int),
        ("step_count", ctypes.c_int),
        ("result_index", ctypes.c_int),
        ("result", ctypes.c_int),
        ("steps", TraceStep * HT_TRACE_MAX_STEPS),
    ]


def load_hash_library(temp_dir):
    library_path = Path(temp_dir) / "libhash_table_gui.so"
    subprocess.run(
        [
            "gcc",
            "-std=c11",
            "-O2",
            "-fPIC",
            "-shared",
            "-DHT_LIBRARY_ONLY",
            str(ROOT / "hash_table.c"),
            "-o",
            str(library_path),
        ],
        check=True,
        cwd=ROOT,
    )
    library = ctypes.CDLL(str(library_path))
    library.ht_new.restype = ctypes.c_void_p
    library.ht_del_hash_table.argtypes = [ctypes.c_void_p]
    for name in ("ht_insert_trace", "ht_search_trace", "ht_delete_trace"):
        function = getattr(library, name)
        function.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(Trace)]
        function.restype = ctypes.c_int
    library.ht_insert_trace.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(Trace),
    ]
    for name in ("ht_table_size", "ht_table_count"):
        getattr(library, name).argtypes = [ctypes.c_void_p]
        getattr(library, name).restype = ctypes.c_int
    library.ht_slot_state.argtypes = [ctypes.c_void_p, ctypes.c_int]
    library.ht_slot_state.restype = ctypes.c_int
    for name in ("ht_slot_key", "ht_slot_value"):
        getattr(library, name).argtypes = [ctypes.c_void_p, ctypes.c_int]
        getattr(library, name).restype = ctypes.c_char_p
    return library


def decode_slot_text(value):
    return value.decode("utf-8", errors="replace") if value else ""


class HashTableWindow:
    def __init__(self, root, library):
        self.root = root
        self.library = library
        self.table = library.ht_new()
        if not self.table:
            raise MemoryError("Unable to allocate the hash table.")

        self.size = library.ht_table_size(self.table)
        self.cells = []
        self.timeline = []
        self.descriptions = []
        self.step_indexes = []
        self.current_stage = 0
        self.play_job = None
        self.autoplay = False
        self.trace = None
        self.operation = ""
        self.key_bytes = b""
        self.value_bytes = b""
        self.last_result = ""

        self.root.title("Hash Table / Probe Studio")
        self.root.configure(bg=COLORS["page"])
        self.root.geometry("1450x900")
        self.root.minsize(1100, 720)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._configure_styles()
        self._build_interface()
        self._render(self._read_table())

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["page"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["page"], foreground=COLORS["ink"], font=("TkDefaultFont", 10))
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["ink"])
        style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"])
        style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"), foreground=COLORS["ink"])
        style.configure("Section.TLabel", font=("TkDefaultFont", 12, "bold"), foreground=COLORS["ink"])
        style.configure("TButton", padding=(10, 7), font=("TkDefaultFont", 10))
        style.configure("Accent.TButton", background=COLORS["green"], foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#115740")])
        style.configure("TEntry", padding=(7, 7))

    def _build_interface(self):
        shell = ttk.Frame(self.root, padding=(22, 18))
        shell.pack(fill="both", expand=True)

        header = ttk.Frame(shell)
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text="Hash Table / Probe Studio", style="Title.TLabel").pack(side="left")
        self.count_label = ttk.Label(header, text="0 / 53 buckets", style="Section.TLabel")
        self.count_label.pack(side="right", padx=(10, 0))
        self.status_label = ttk.Label(header, text="READY", foreground=COLORS["green"])
        self.status_label.pack(side="right")

        workspace = ttk.Frame(shell)
        workspace.pack(fill="both", expand=True)
        workspace.columnconfigure(0, weight=3, minsize=650)
        workspace.columnconfigure(1, weight=2, minsize=360)
        workspace.rowconfigure(0, weight=1)

        board_panel = ttk.Frame(workspace, style="Panel.TFrame", padding=16)
        board_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        inspector = ttk.Frame(workspace, style="Panel.TFrame", padding=16)
        inspector.grid(row=0, column=1, sticky="nsew")

        board_header = ttk.Frame(board_panel, style="Panel.TFrame")
        board_header.pack(fill="x", pady=(0, 12))
        ttk.Label(board_header, text="Bucket array", style="Section.TLabel").pack(side="left")
        ttk.Label(board_header, text="53 fixed slots · open addressing", style="Muted.TLabel").pack(side="right")

        controls = ttk.Frame(board_panel, style="Panel.TFrame")
        controls.pack(fill="x", pady=(0, 12))
        ttk.Label(controls, text="Key", style="Muted.TLabel").pack(side="left", padx=(0, 5))
        self.key_entry = ttk.Entry(controls, width=18)
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.key_entry.bind("<Return>", lambda _event: self.insert())
        ttk.Label(controls, text="Value", style="Muted.TLabel").pack(side="left", padx=(0, 5))
        self.value_entry = ttk.Entry(controls, width=18)
        self.value_entry.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.value_entry.bind("<Return>", lambda _event: self.insert())
        ttk.Button(controls, text="Insert / update", style="Accent.TButton", command=self.insert).pack(side="left", padx=(0, 5))
        ttk.Button(controls, text="Search", command=self.search).pack(side="left", padx=(0, 5))
        ttk.Button(controls, text="Delete", command=self.delete).pack(side="left")

        legend = ttk.Frame(board_panel, style="Panel.TFrame")
        legend.pack(side="bottom", fill="x", pady=(12, 0))
        self._legend_item(legend, "#f7f9f8", "Empty").pack(side="left", padx=(0, 15))
        self._legend_item(legend, "#e2f2e9", "Occupied").pack(side="left", padx=(0, 15))
        self._legend_item(legend, "#f8e4df", "Deleted marker").pack(side="left", padx=(0, 15))
        self._legend_item(legend, "#ffe0a6", "Current probe").pack(side="left")

        self.board = tk.Frame(board_panel, bg=COLORS["panel"])
        self.board.pack(fill="both", expand=True)
        for column in range(9):
            self.board.grid_columnconfigure(column, weight=1, uniform="bucket")
        for row in range((self.size + 8) // 9):
            self.board.grid_rowconfigure(row, weight=1, uniform="bucket")
        for index in range(self.size):
            cell = tk.Frame(
                self.board,
                bg=COLORS["empty"],
                highlightthickness=1,
                highlightbackground=COLORS["line"],
                padx=7,
                pady=5,
            )
            cell.grid(row=index // 9, column=index % 9, sticky="nsew", padx=3, pady=3)
            index_label = tk.Label(cell, text=f"{index:02d}", bg=COLORS["empty"], fg=COLORS["muted"], anchor="w", font=("TkDefaultFont", 8, "bold"))
            index_label.pack(fill="x")
            key_label = tk.Label(cell, text="empty", bg=COLORS["empty"], fg=COLORS["muted"], anchor="w", font=("TkDefaultFont", 9, "bold"), wraplength=110)
            key_label.pack(fill="x", pady=(4, 0))
            value_label = tk.Label(cell, text="", bg=COLORS["empty"], fg=COLORS["muted"], anchor="w", font=("TkDefaultFont", 8), wraplength=110)
            value_label.pack(fill="x")
            self.cells.append((cell, index_label, key_label, value_label))

        ttk.Label(inspector, text="Operation trace", style="Section.TLabel").pack(anchor="w")
        ttk.Label(inspector, text="Double hash · polynomial rolling hash", style="Muted.TLabel").pack(anchor="w", pady=(3, 10))
        self.hash_text = tk.Text(inspector, height=10, wrap="word", bg="#f7f9f8", fg=COLORS["ink"], relief="flat", padx=10, pady=9, font=("TkFixedFont", 9))
        self.hash_text.pack(fill="x")
        self.hash_text.configure(state="disabled")

        timeline_bar = ttk.Frame(inspector, style="Panel.TFrame")
        timeline_bar.pack(fill="x", pady=(14, 5))
        ttk.Label(timeline_bar, text="Stage", style="Section.TLabel").pack(side="left")
        self.stage_label = ttk.Label(timeline_bar, text="No operation", style="Muted.TLabel")
        self.stage_label.pack(side="right")

        playback = ttk.Frame(inspector, style="Panel.TFrame")
        playback.pack(fill="x", pady=(0, 10))
        ttk.Button(playback, text="Start", command=self.to_start).pack(side="left", padx=(0, 5))
        ttk.Button(playback, text="Back", command=self.previous_stage).pack(side="left", padx=(0, 5))
        self.play_button = ttk.Button(playback, text="Play", command=self.toggle_play)
        self.play_button.pack(side="left", padx=(0, 5))
        ttk.Button(playback, text="Next", command=self.next_stage).pack(side="left", padx=(0, 5))
        ttk.Button(playback, text="End", command=self.to_end).pack(side="left")

        self.description = tk.StringVar(value="Insert a key, search for it, or delete it to inspect the probe path.")
        ttk.Label(inspector, textvariable=self.description, style="Panel.TLabel", wraplength=355, justify="left").pack(anchor="w", fill="x", pady=(0, 11))

        ttk.Label(inspector, text="Probe sequence", style="Section.TLabel").pack(anchor="w")
        self.probe_list = tk.Listbox(inspector, height=12, bg="#f7f9f8", fg=COLORS["ink"], relief="flat", font=("TkFixedFont", 9), activestyle="none", selectbackground=COLORS["blue_light"])
        self.probe_list.pack(fill="both", expand=True, pady=(6, 0))

    @staticmethod
    def _legend_item(parent, color, label):
        item = ttk.Frame(parent, style="Panel.TFrame")
        swatch = tk.Label(item, text="  ", bg=color, relief="solid", borderwidth=1)
        swatch.pack(side="left", padx=(0, 5))
        ttk.Label(item, text=label, style="Muted.TLabel").pack(side="left")
        return item

    def _read_table(self):
        buckets = []
        for index in range(self.size):
            state = self.library.ht_slot_state(self.table, index)
            key = decode_slot_text(self.library.ht_slot_key(self.table, index))
            value = decode_slot_text(self.library.ht_slot_value(self.table, index))
            buckets.append((state, key, value))
        return buckets

    def _render(self, buckets, active_index=-1, visited_indexes=()):
        visited = set(visited_indexes)
        occupied = 0
        for index, (state, key, value) in enumerate(buckets):
            cell, index_label, key_label, value_label = self.cells[index]
            if state == HT_SLOT_OCCUPIED:
                occupied += 1
                background = COLORS["green_light"]
                key_text = key
                value_text = value if value else "(empty value)"
            elif state == HT_SLOT_DELETED:
                background = COLORS["red_light"]
                key_text = "deleted"
                value_text = "tombstone"
            else:
                background = COLORS["empty"]
                key_text = "empty"
                value_text = ""

            if index in visited:
                background = COLORS["blue_light"]
            if index == active_index:
                background = COLORS["amber"]
            for widget in (cell, index_label, key_label, value_label):
                widget.configure(bg=background)
            cell.configure(highlightbackground=COLORS["green"] if index == active_index else COLORS["line"], highlightthickness=2 if index == active_index else 1)
            key_label.configure(text=key_text)
            value_label.configure(text=value_text)
        self.count_label.configure(text=f"{occupied} / {self.size} buckets")

    def _set_hash_explanation(self, key, trace):
        content = [
            f"Key: {key!r}",
            "h = (h * base + byte) mod 53",
            f"h1 (base 151) = {trace.hash_a}  -> start bucket",
            f"h2 (base 163) = {trace.hash_b}",
            f"stride = (h2 + 1) mod 53 = {trace.stride}",
            f"probe(i) = (h1 + i * stride) mod 53",
            "",
            "Hash each UTF-8 byte in order:",
        ]
        hash_a = 0
        hash_b = 0
        for byte in key.encode("utf-8"):
            hash_a = (hash_a * 151 + byte) % self.size
            hash_b = (hash_b * 163 + byte) % self.size
            char = chr(byte) if 32 <= byte < 127 else f"\\x{byte:02x}"
            content.append(f"{char!r} ({byte:3d})  h1={hash_a:2d}  h2={hash_b:2d}")
        self.hash_text.configure(state="normal")
        self.hash_text.delete("1.0", "end")
        self.hash_text.insert("1.0", "\n".join(content))
        self.hash_text.configure(state="disabled")

    def _prepare_operation(self, operation, key, value=""):
        key_bytes = key.encode("utf-8")
        value_bytes = value.encode("utf-8")
        if not key:
            messagebox.showwarning("Key required", "Enter a key before running an operation.", parent=self.root)
            return
        if len(key_bytes) >= HT_KEY_MAX or len(value_bytes) >= HT_KEY_MAX:
            messagebox.showwarning("Input too long", "Keys and values must be shorter than 256 UTF-8 bytes.", parent=self.root)
            return

        self._stop_playback()
        before = self._read_table()
        trace = Trace()
        encoded_key = key_bytes + b"\0"
        encoded_value = value_bytes + b"\0"
        if operation == "insert":
            result = self.library.ht_insert_trace(self.table, encoded_key, encoded_value, ctypes.byref(trace))
        elif operation == "search":
            result = self.library.ht_search_trace(self.table, encoded_key, ctypes.byref(trace))
        else:
            result = self.library.ht_delete_trace(self.table, encoded_key, ctypes.byref(trace))

        self.trace = trace
        self.operation = operation
        self.key_bytes = key_bytes
        self.value_bytes = value_bytes
        self._set_hash_explanation(key, trace)
        self._build_timeline(before, operation, result)
        self._populate_probe_list()
        self.current_stage = 0
        self._show_stage()

    def _build_timeline(self, before, operation, result):
        buckets = list(before)
        self.timeline = [list(buckets)]
        self.descriptions = [f"Before {operation}: begin at bucket {self.trace.start_index}."]
        self.step_indexes = [-1]

        for attempt in range(self.trace.step_count):
            step = self.trace.steps[attempt]
            self.step_indexes.append(step.index)
            if step.action == HT_TRACE_EMPTY:
                detail = f"Bucket {step.index} is empty. The probe search stops here."
            elif step.action == HT_TRACE_COLLISION:
                detail = f"Collision at {step.index}: {decode_slot_text(step.key)} is stored here. Continue by stride {self.trace.stride}."
            elif step.action == HT_TRACE_TOMBSTONE:
                detail = f"Bucket {step.index} is a tombstone. Keep probing so later keys remain reachable."
            elif step.action == HT_TRACE_FOUND:
                detail = f"Match at bucket {step.index}: value is {decode_slot_text(step.value)!r}."
            elif step.action == HT_TRACE_UPDATED:
                detail = f"Key already exists at bucket {step.index}; replace its value."
            elif step.action == HT_TRACE_DELETED:
                detail = f"Match at bucket {step.index}; mark the slot deleted, not empty."
            else:
                detail = f"Bucket {step.index} is empty, so the key is not present."
            self.descriptions.append(f"Probe {attempt}: {detail}")
            self.timeline.append(list(buckets))

        if operation == "insert" and result in (HT_RESULT_INSERTED, HT_RESULT_UPDATED):
            target = self.trace.result_index
            buckets[target] = (HT_SLOT_OCCUPIED, self.key_bytes.decode("utf-8", errors="replace"), self.value_bytes.decode("utf-8", errors="replace"))
            action = "Inserted" if result == HT_RESULT_INSERTED else "Updated"
            self.timeline.append(list(buckets))
            self.step_indexes.append(target)
            self.descriptions.append(f"{action} the key/value pair in bucket {target}.")
            self.last_result = f"{action} at bucket {target}."
        elif operation == "delete" and result == HT_RESULT_UPDATED:
            target = self.trace.result_index
            buckets[target] = (HT_SLOT_DELETED, "", "")
            self.timeline.append(list(buckets))
            self.step_indexes.append(target)
            self.descriptions.append(f"Bucket {target} is now a tombstone.")
            self.last_result = f"Deleted from bucket {target}; a tombstone keeps the probe chain intact."
        elif operation == "search" and result == HT_RESULT_UPDATED:
            self.last_result = f"Found in bucket {self.trace.result_index}."
        elif result == HT_RESULT_FULL:
            self.last_result = "The table is full; no bucket was changed."
        else:
            self.last_result = f"Key {self.key_bytes.decode('utf-8', errors='replace')!r} was not found."

    def _populate_probe_list(self):
        self.probe_list.delete(0, "end")
        for attempt in range(self.trace.step_count):
            step = self.trace.steps[attempt]
            if step.action == HT_TRACE_COLLISION:
                outcome = f"collision: {decode_slot_text(step.key)}"
            elif step.action == HT_TRACE_TOMBSTONE:
                outcome = "tombstone; continue"
            elif step.action == HT_TRACE_FOUND:
                outcome = "key found"
            elif step.action == HT_TRACE_UPDATED:
                outcome = "key exists; update"
            elif step.action == HT_TRACE_DELETED:
                outcome = "key found; delete"
            elif step.action == HT_TRACE_EMPTY:
                outcome = "empty slot"
            else:
                outcome = "empty slot; miss"
            self.probe_list.insert("end", f"i={attempt:02d}  bucket {step.index:02d}  {outcome}")
        self.probe_list.insert("end", "")
        self.probe_list.insert("end", self.last_result)

    def _show_stage(self):
        if not self.timeline:
            return
        self.current_stage = max(0, min(self.current_stage, len(self.timeline) - 1))
        active = self.step_indexes[self.current_stage]
        visited = self.step_indexes[1 : self.current_stage + 1]
        self._render(self.timeline[self.current_stage], active, visited)
        self.stage_label.configure(text=f"{self.current_stage} / {len(self.timeline) - 1}")
        self.description.set(self.descriptions[self.current_stage])
        self.status_label.configure(text=self.operation.upper())
        if self.current_stage > 0:
            self.probe_list.selection_clear(0, "end")
            probe_row = self.current_stage - 1
            if probe_row < self.trace.step_count:
                self.probe_list.selection_set(probe_row)
                self.probe_list.see(probe_row)

    def to_start(self):
        self._stop_playback()
        self.current_stage = 0
        self._show_stage()

    def previous_stage(self):
        self._stop_playback()
        self.current_stage -= 1
        self._show_stage()

    def next_stage(self):
        self.current_stage += 1
        self._show_stage()

    def to_end(self):
        self._stop_playback()
        self.current_stage = len(self.timeline) - 1
        self._show_stage()

    def toggle_play(self):
        if self.autoplay:
            self._stop_playback()
            return
        if not self.timeline or self.current_stage >= len(self.timeline) - 1:
            self.to_start()
        self.autoplay = True
        self.play_button.configure(text="Pause")
        self._play_next()

    def _play_next(self):
        if not self.autoplay:
            return
        if self.current_stage >= len(self.timeline) - 1:
            self._stop_playback()
            return
        self.current_stage += 1
        self._show_stage()
        self.play_job = self.root.after(700, self._play_next)

    def _stop_playback(self):
        self.autoplay = False
        self.play_button.configure(text="Play")
        if self.play_job is not None:
            self.root.after_cancel(self.play_job)
            self.play_job = None

    def insert(self):
        self._prepare_operation("insert", self.key_entry.get(), self.value_entry.get())

    def search(self):
        self._prepare_operation("search", self.key_entry.get())

    def delete(self):
        self._prepare_operation("delete", self.key_entry.get())

    def close(self):
        self._stop_playback()
        if self.table:
            self.library.ht_del_hash_table(self.table)
            self.table = None
        self.root.destroy()


def main():
    try:
        temp_dir = tempfile.TemporaryDirectory(prefix="hash-table-gui-")
        library = load_hash_library(temp_dir.name)
    except (OSError, subprocess.CalledProcessError) as error:
        messagebox.showerror("Unable to start", f"Could not compile the hash table.\n\n{error}")
        return

    root = tk.Tk()
    try:
        HashTableWindow(root, library)
    except MemoryError as error:
        messagebox.showerror("Unable to start", str(error), parent=root)
        root.destroy()
        temp_dir.cleanup()
        return
    root.mainloop()
    temp_dir.cleanup()


if __name__ == "__main__":
    main()