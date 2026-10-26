import tkinter as tk
from tkinter import ttk


BUCKET_COUNT = 53
HASH_PRIME_1 = 151
HASH_PRIME_2 = 163
DELETED = object()

COLORS = {
    "background": "#f2f4ef",
    "paper": "#ffffff",
    "ink": "#202c2b",
    "muted": "#65716d",
    "line": "#dce3dc",
    "green": "#28705c",
    "green_light": "#e4f1e9",
    "blue": "#376b91",
    "blue_light": "#e8f0f6",
    "orange": "#a35a28",
    "orange_light": "#fbefe3",
}


class HashTableTeacher:
    def __init__(self, root):
        self.root = root
        self.root.title("Hash Table, Step by Step")
        self.root.geometry("1240x790")
        self.root.minsize(980, 680)
        self.root.configure(bg=COLORS["background"])

        self.buckets = [None for _ in range(BUCKET_COUNT)]
        self.trace = []
        self.trace_index = 0
        self.active_bucket = None
        self.message_var = tk.StringVar(value="hello")
        self.value_var = tk.StringVar(value="world")
        self.status_var = tk.StringVar(value="Add a message to see how it is stored.")
        self.count_var = tk.StringVar(value="0 / 53 items")
        self.bucket_cells = []
        self.slot_var = tk.StringVar(value="Select a slot to inspect it.")
        self.hash_a_var = tk.StringVar(value="Waiting for key")
        self.hash_b_var = tk.StringVar(value="Waiting for key")
        self.probe_slots = []
        self.collision_slots = set()
        self.tombstone_slots = set()
        self.visual_buckets = None
        self.item_count = 0

        self._configure_styles()
        self._build_interface()
        self._render_buckets()
        self._show_empty_trace()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["background"])
        style.configure(
            "Panel.TFrame", background=COLORS["paper"], relief="flat"
        )
        style.configure(
            "TLabel",
            background=COLORS["background"],
            foreground=COLORS["ink"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Panel.TLabel",
            background=COLORS["paper"],
            foreground=COLORS["ink"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=COLORS["background"],
            foreground=COLORS["ink"],
            font=("Georgia", 23, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["background"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=COLORS["paper"],
            foreground=COLORS["ink"],
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "TButton", font=("Segoe UI", 10, "bold"), padding=(10, 7)
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["green"],
            foreground="white",
            borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", "#205b49")])
        style.configure("TEntry", padding=8, font=("Segoe UI", 11))

    def _build_interface(self):
        header = ttk.Frame(self.root, padding=(18, 12, 18, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Hash Table, Step by Step", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Calculate two hashes, follow the probe sequence, and watch 53 slots fill.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        notice = tk.Label(
            self.root,
            text="A hash is not encryption: it chooses where a message goes; it does not hide or scramble the message.",
            bg=COLORS["orange_light"],
            fg=COLORS["orange"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=10,
            pady=6,
        )
        notice.pack(fill="x", padx=18, pady=(0, 9))

        self._build_controls(self.root)

        content = ttk.Frame(self.root, padding=(18, 0, 18, 10))
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3, minsize=510)
        content.columnconfigure(1, weight=2, minsize=340)
        content.rowconfigure(0, weight=1)

        self._build_table(content, 0)
        self._build_walkthrough(content, 1)

        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=COLORS["ink"],
            fg="white",
            font=("Segoe UI", 10),
            anchor="w",
            padx=18,
            pady=7,
        )
        status.pack(fill="x", side="bottom")

    def _panel(self, parent, column, title):
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        panel.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
        panel.columnconfigure(0, weight=1)
        ttk.Label(panel, text=title, style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )
        return panel

    def _build_controls(self, parent):
        controls = ttk.Frame(parent, padding=(18, 0, 18, 10))
        controls.pack(fill="x")
        controls.columnconfigure(0, weight=1, uniform="input")
        controls.columnconfigure(1, weight=1, uniform="input")
        key_entry = ttk.Entry(controls, textvariable=self.message_var)
        key_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        key_entry.bind("<Return>", lambda _event: self.insert_message())
        self.message_entry = key_entry
        ttk.Entry(controls, textvariable=self.value_var).grid(
            row=0, column=1, sticky="ew", padx=4
        )

        ttk.Button(
            controls,
            text="Insert / update",
            style="Accent.TButton",
            command=self.insert_message,
        ).grid(row=0, column=2, padx=3)
        ttk.Button(controls, text="Search", command=self.search_message).grid(
            row=0, column=3, padx=3
        )
        ttk.Button(controls, text="Delete", command=self.delete_message).grid(
            row=0, column=4, padx=3
        )
        ttk.Button(controls, text="Demo", command=self.load_demo).grid(
            row=0, column=5, padx=3
        )
        ttk.Button(controls, text="Clear", command=self.clear_table).grid(
            row=0, column=6, padx=(3, 0)
        )
        tk.Label(
            controls,
            text="Key",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=(2, 0))
        tk.Label(
            controls,
            text="Value",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=1, sticky="w", padx=(6, 0))

    def _build_table(self, parent, column):
        panel = self._panel(parent, column, "53 slots · open addressing")
        panel.columnconfigure(1, weight=1)
        ttk.Label(panel, textvariable=self.count_var, style="Panel.TLabel").grid(
            row=0, column=1, sticky="e", pady=(0, 8)
        )
        tk.Label(
            panel,
            text=f"Next slot = (start + attempt x jump) mod {BUCKET_COUNT}",
            bg=COLORS["green_light"],
            fg=COLORS["green"],
            font=("Consolas", 9, "bold"),
            padx=8,
            pady=6,
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        bucket_grid = tk.Frame(panel, bg=COLORS["paper"])
        bucket_grid.grid(row=2, column=0, columnspan=2, sticky="nsew")
        for grid_column in range(7):
            bucket_grid.columnconfigure(grid_column, weight=1, uniform="bucket")
        for grid_row in range(8):
            bucket_grid.rowconfigure(grid_row, weight=1, uniform="bucket")
        for index in range(BUCKET_COUNT):
            cell = tk.Frame(
                bucket_grid,
                bg=COLORS["paper"],
                highlightthickness=1,
                highlightbackground=COLORS["line"],
                padx=3,
                pady=2,
            )
            cell.grid(row=index // 7, column=index % 7, sticky="nsew", padx=2, pady=2)
            cell.rowconfigure(1, weight=1)
            cell.columnconfigure(0, weight=1)
            index_label = tk.Label(
                cell,
                text=f"{index:02}",
                bg=COLORS["paper"],
                fg=COLORS["muted"],
                font=("Consolas", 8, "bold"),
                anchor="w",
            )
            index_label.grid(row=0, column=0, sticky="ew")
            contents = tk.Label(
                cell,
                text="empty",
                bg=COLORS["paper"],
                fg="#9aa49f",
                font=("Segoe UI", 8),
                anchor="center",
                justify="center",
                wraplength=92,
            )
            contents.grid(row=1, column=0, sticky="nsew")
            self.bucket_cells.append((cell, index_label, contents))
            for widget in (cell, index_label, contents):
                widget.bind("<Button-1>", lambda _event, i=index: self.select_bucket(i))
        legend = tk.Frame(panel, bg=COLORS["paper"])
        legend.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(7, 0))
        for text, color in (
            ("current", COLORS["green_light"]),
            ("checked", COLORS["blue_light"]),
            ("collision / deleted", COLORS["orange_light"]),
        ):
            tk.Label(
                legend,
                text=text,
                bg=color,
                fg=COLORS["ink"],
                font=("Segoe UI", 8),
                padx=5,
                pady=2,
            ).pack(side="left", padx=(0, 4))
        panel.rowconfigure(2, weight=1)
        tk.Label(
            panel,
            textvariable=self.slot_var,
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=560,
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(7, 0))

    def _build_walkthrough(self, parent, column):
        panel = self._panel(parent, column, "Follow the calculations")
        panel.rowconfigure(3, weight=1)
        self.step_title = tk.Label(
            panel,
            text="1. Calculate two different clues",
            bg=COLORS["blue_light"],
            fg=COLORS["blue"],
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            padx=10,
            pady=9,
        )
        self.step_title.grid(row=1, column=0, sticky="ew", pady=(0, 7))

        hash_cards = tk.Frame(panel, bg=COLORS["paper"])
        hash_cards.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        hash_cards.columnconfigure((0, 1), weight=1, uniform="hash-card")
        self.hash_a_card = tk.Label(
            hash_cards,
            textvariable=self.hash_a_var,
            bg=COLORS["blue_light"],
            fg=COLORS["blue"],
            font=("Segoe UI", 9, "bold"),
            justify="left",
            anchor="w",
            padx=8,
            pady=7,
        )
        self.hash_a_card.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.hash_b_card = tk.Label(
            hash_cards,
            textvariable=self.hash_b_var,
            bg=COLORS["orange_light"],
            fg=COLORS["orange"],
            font=("Segoe UI", 9, "bold"),
            justify="left",
            anchor="w",
            padx=8,
            pady=7,
        )
        self.hash_b_card.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.step_text = tk.Text(
            panel,
            wrap="word",
            height=11,
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=("Consolas", 10),
            relief="flat",
            padx=4,
            pady=4,
            state="disabled",
        )
        self.step_text.grid(row=3, column=0, sticky="nsew")

        navigation = ttk.Frame(panel, style="Panel.TFrame")
        navigation.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        navigation.columnconfigure((0, 1), weight=1)
        ttk.Button(navigation, text="Previous", command=self.previous_step).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(navigation, text="Next", command=self.next_step).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        self.step_counter = ttk.Label(panel, text="No steps yet", style="Panel.TLabel")
        self.step_counter.grid(row=5, column=0, sticky="e", pady=(6, 0))

    def _hash_with_base(self, key, base, label):
        value = 0
        purpose = (
            "This result is the first slot to check."
            if label == "h1"
            else "This result plus 1 is the jump distance after a collision."
        )
        steps = [
            {
                "title": (
                    "Hash 1: find the first slot"
                    if label == "h1"
                    else "Hash 2: calculate the jump distance"
                ),
                "text": (
                    f"We run the same character calculation with base {base}.\n\n"
                    f"Why? {purpose}\n\nStart with h = 0."
                ),
                "bucket": None,
                "hash_lane": label,
                "hash_value": 0,
            }
        ]
        for position, character in enumerate(key):
            code = ord(character)
            exponent = len(key) - position - 1
            power = base**exponent
            term = code * power
            total = value + term
            remainder = total % BUCKET_COUNT
            steps.append(
                {
                    "title": (
                        f"Hash 1 · character {position + 1} of {len(key)}"
                        if label == "h1"
                        else f"Hash 2 · character {position + 1} of {len(key)}"
                    ),
                    "text": (
                        f"Character {character!r} has number {code}.\n\n"
                        f"Its place in the key gives exponent {exponent}:\n"
                        f"{base}^{exponent} = {power}\n"
                        f"This character adds {code} x {power} = {term}.\n\n"
                        f"Add that to the running total: {value} + {term} = {total}\n"
                        f"Divide by {BUCKET_COUNT} and keep only the remainder:\n"
                        f"{total} = {BUCKET_COUNT} x {total // BUCKET_COUNT} + {remainder}\n\n"
                        f"Running remainder for {label}: {remainder}\n\n{purpose}"
                    ),
                    "bucket": None,
                    "hash_lane": label,
                    "hash_value": remainder,
                }
            )
            value = remainder
        return value, steps

    def _hash_message(self, key):
        hash_a, steps_a = self._hash_with_base(key, HASH_PRIME_1, "h1")
        hash_b, steps_b = self._hash_with_base(key, HASH_PRIME_2, "h2")
        steps = steps_a + steps_b
        steps.append(
            {
                "title": "The two results have different jobs",
                "text": (
                    f"Hash 1 gives first slot: {hash_a}\n"
                    f"Hash 2 gives jump distance: {hash_b} + 1 = {hash_b + 1}\n\n"
                    "The +1 guarantees the jump is not zero.\n"
                    "Attempt 0 starts at the first slot. After a collision, "
                    "attempt 1 adds one jump; attempt 2 adds two jumps."
                ),
                "bucket": hash_a,
                "hash_results": (hash_a, hash_b),
            }
        )
        return hash_a, hash_b, steps

    @staticmethod
    def _probe_index(hash_a, hash_b, attempt):
        return (hash_a + attempt * (hash_b + 1)) % BUCKET_COUNT

    @staticmethod
    def _hash_value(key, base):
        value = 0
        for position, character in enumerate(key):
            exponent = len(key) - position - 1
            value = (value + ord(character) * base**exponent) % BUCKET_COUNT
        return value

    def _set_trace(self, trace, status):
        self.trace = trace
        self.trace_index = 0
        self.status_var.set(status)
        self._show_trace_step()

    def _snapshot_table(self):
        return tuple(self.buckets)

    def _attach_table_history(self, trace, initial_state, final_state=None):
        for step in trace:
            step["table_state"] = initial_state
        if trace and final_state is not None:
            trace[-1]["table_state"] = final_state

    def _show_empty_trace(self):
        self.step_title.configure(text="Ready")
        self.step_text.configure(state="normal")
        self.step_text.delete("1.0", "end")
        self.step_text.insert(
            "1.0",
            "Enter a key and value, then insert, search, or delete.\n\n"
            "The walkthrough computes both polynomial hashes, shows each character's "
            "contribution, then follows the double-hash probe sequence.",
        )
        self.step_text.configure(state="disabled")
        self.step_counter.configure(text="No steps yet")

    def _show_trace_step(self):
        if not self.trace:
            self._show_empty_trace()
            return
        step = self.trace[self.trace_index]
        self.step_title.configure(text=step["title"])
        self.step_text.configure(state="normal")
        self.step_text.delete("1.0", "end")
        self.step_text.insert("1.0", step["text"])
        self.step_text.configure(state="disabled")
        self.step_counter.configure(
            text=f"Step {self.trace_index + 1} of {len(self.trace)}"
        )
        hash_values = {}
        visible_table = self.trace[0].get("table_state", self.buckets)
        self.probe_slots = []
        self.collision_slots = set()
        self.tombstone_slots = set()
        for earlier_step in self.trace[: self.trace_index + 1]:
            if "table_state" in earlier_step:
                visible_table = earlier_step["table_state"]
            lane = earlier_step.get("hash_lane")
            if lane:
                hash_values[lane] = earlier_step["hash_value"]
            if "hash_results" in earlier_step:
                hash_values["h1"], hash_values["h2"] = earlier_step["hash_results"]
            title = earlier_step["title"]
            bucket = earlier_step.get("bucket")
            if bucket is None:
                continue
            if title.startswith(("Probe attempt", "Check probe")):
                if bucket not in self.probe_slots:
                    self.probe_slots.append(bucket)
            elif title.startswith("Collision at slot"):
                self.collision_slots.add(bucket)
            elif title == "Skip deleted slot":
                self.tombstone_slots.add(bucket)
        first_value = hash_values.get("h1")
        second_value = hash_values.get("h2")
        self.hash_a_var.set(
            "FIRST SLOT · base 151\n"
            + (f"h1 = {first_value}" if first_value is not None else "not calculated yet")
        )
        self.hash_b_var.set(
            "JUMP SIZE · base 163\n"
            + (
                f"h2 + 1 = {second_value + 1}"
                if second_value is not None
                else "h2 + 1 · not calculated yet"
            )
        )
        if step.get("bucket") is not None and (
            step.get("hash_results")
            or step["title"].startswith(
                ("Probe attempt", "Check probe", "Collision", "Store", "Update", "Key matches", "Stop", "Skip")
            )
        ):
            self.active_bucket = step["bucket"]
        else:
            self.active_bucket = None
        self.visual_buckets = visible_table
        self._render_buckets()

    def previous_step(self):
        if self.trace and self.trace_index > 0:
            self.trace_index -= 1
            self._show_trace_step()

    def next_step(self):
        if self.trace and self.trace_index < len(self.trace) - 1:
            self.trace_index += 1
            self._show_trace_step()

    def select_bucket(self, index):
        self.active_bucket = index
        self._render_buckets()
        self.status_var.set(f"Selected bucket {index}.")

    def _render_buckets(self):
        visible_buckets = self.visual_buckets if self.visual_buckets is not None else self.buckets
        visible_count = sum(
            item is not None and item is not DELETED for item in visible_buckets
        )
        self.count_var.set(f"{visible_count} / {BUCKET_COUNT} items")
        for index, (cell, index_label, contents) in enumerate(self.bucket_cells):
            active = index == self.active_bucket
            if index in self.collision_slots or index in self.tombstone_slots:
                background = COLORS["orange_light"]
                border = COLORS["orange"]
            elif active:
                background = COLORS["green_light"]
                border = COLORS["green"]
            elif index in self.probe_slots:
                background = COLORS["blue_light"]
                border = COLORS["blue"]
            else:
                background = COLORS["paper"]
                border = COLORS["line"]
            cell.configure(bg=background, highlightbackground=border)
            index_label.configure(
                bg=background,
                fg=COLORS["green"] if active else COLORS["muted"],
            )
            item = visible_buckets[index]
            if item is None:
                contents.configure(
                    text="empty", bg=background, fg="#9aa49f", font=("Segoe UI", 8)
                )
                continue
            if item is DELETED:
                contents.configure(
                    text="deleted", bg=COLORS["orange_light"],
                    fg=COLORS["orange"], font=("Segoe UI", 8, "bold")
                )
                continue
            key, value = item
            key_label = key if len(key) <= 7 else key[:6] + "..."
            value_label = value if len(value) <= 7 else value[:6] + "..."
            contents.configure(
                text=f"{key_label}\n{value_label}",
                bg=background,
                fg=COLORS["green"] if active else COLORS["blue"],
                font=("Segoe UI", 8, "bold"),
            )
        if self.active_bucket is None:
            self.slot_var.set("Select a slot to inspect its key and value.")
        else:
            item = visible_buckets[self.active_bucket]
            if item is None:
                details = "empty slot"
            elif item is DELETED:
                details = "deleted marker (tombstone)"
            else:
                details = f"key = {item[0]!r}, value = {item[1]!r}"
            self.slot_var.set(f"Slot {self.active_bucket}: {details}")

    def insert_message(self):
        key = self.message_var.get()
        value = self.value_var.get()
        if not key:
            self.status_var.set("Enter a key first.")
            return
        trace, result = self._insert_item(key, value)
        self._set_trace(trace, result)

    def _insert_item(self, key, value):
        initial_state = self._snapshot_table()
        hash_a, hash_b, trace = self._hash_message(key)
        visited = set()
        for attempt in range(BUCKET_COUNT):
            index = self._probe_index(hash_a, hash_b, attempt)
            trace.append(
                {
                    "title": f"Probe attempt {attempt}: slot {index}",
                    "text": (
                        f"index = (h1 + attempt x (h2 + 1)) mod {BUCKET_COUNT}\n"
                        f"index = ({hash_a} + {attempt} x ({hash_b} + 1)) mod {BUCKET_COUNT}\n"
                        f"index = {index}\n\n"
                        "Attempt 0 is the original hash. Each collision increases "
                        "attempt by 1."
                    ),
                    "bucket": index,
                }
            )
            if index in visited:
                trace.append(
                    {
                        "title": "Probe sequence repeated",
                        "text": "This double-hash step revisits a slot before finding an empty one.",
                        "bucket": index,
                    }
                )
                break
            visited.add(index)
            item = self.buckets[index]
            if item is None or item is DELETED:
                was_new = item is None
                self.buckets[index] = (key, value)
                if was_new:
                    self.item_count += 1
                trace.append(
                    {
                        "title": "Store the key-value pair",
                        "text": (
                            f"Slot {index} is {'empty' if was_new else 'a deleted slot'}.\n\n"
                            f"Store key {key!r} with value {value!r} here."
                        ),
                        "bucket": index,
                    }
                )
                self._render_buckets()
                self._attach_table_history(
                    trace, initial_state, self._snapshot_table()
                )
                return trace, f"Stored {key!r} at slot {index}."
            if item[0] == key:
                self.buckets[index] = (key, value)
                trace.append(
                    {
                        "title": "Update existing key",
                        "text": (
                            f"Slot {index} already has key {key!r}.\n\n"
                            f"Replace its value {item[1]!r} with {value!r}; "
                            "do not create a second entry."
                        ),
                        "bucket": index,
                    }
                )
                self._render_buckets()
                self._attach_table_history(
                    trace, initial_state, self._snapshot_table()
                )
                return trace, f"Updated {key!r} at slot {index}."
            trace.append(
                {
                    "title": f"Collision at slot {index}",
                    "text": (
                        f"This slot contains a different key: {item[0]!r}.\n\n"
                        "Do not overwrite it. Increase attempt and use the second hash "
                        "to calculate the next slot."
                    ),
                    "bucket": index,
                }
            )
        self._render_buckets()
        self._attach_table_history(trace, initial_state)
        return trace, "No reachable empty slot was found."

    def search_message(self):
        key = self.message_var.get()
        if not key:
            self.status_var.set("Enter a key to search for.")
            return
        trace, result = self._find_item(key, delete=False)
        self._set_trace(trace, result)

    def delete_message(self):
        key = self.message_var.get()
        if not key:
            self.status_var.set("Enter a key to delete.")
            return
        trace, result = self._find_item(key, delete=True)
        self._set_trace(trace, result)

    def _find_item(self, key, delete):
        initial_state = self._snapshot_table()
        hash_a, hash_b, trace = self._hash_message(key)
        visited = set()
        for attempt in range(BUCKET_COUNT):
            index = self._probe_index(hash_a, hash_b, attempt)
            trace.append(
                {
                    "title": f"Check probe {attempt}: slot {index}",
                    "text": (
                        f"index = ({hash_a} + {attempt} x ({hash_b} + 1)) mod "
                        f"{BUCKET_COUNT} = {index}\n\n"
                        f"Look at slot {index} in the table."
                    ),
                    "bucket": index,
                }
            )
            if index in visited:
                break
            visited.add(index)
            item = self.buckets[index]
            if item is None:
                trace.append(
                    {
                        "title": "Stop at an empty slot",
                        "text": (
                            f"Slot {index} is empty. No matching key can appear later "
                            "in this probe sequence."
                        ),
                        "bucket": index,
                    }
                )
                break
            if item is DELETED:
                trace.append(
                    {
                        "title": "Skip deleted slot",
                        "text": (
                            f"Slot {index} is a tombstone. Keep probing: an item "
                            "further along the sequence may still be the key."
                        ),
                        "bucket": index,
                    }
                )
                continue
            if item[0] == key:
                if delete:
                    self.buckets[index] = DELETED
                    self.item_count -= 1
                    action = "Delete the item and leave a tombstone."
                    result = f"Deleted {key!r}; slot {index} is marked deleted."
                else:
                    action = f"Found value {item[1]!r}."
                    result = f"Found {key!r}: {item[1]!r}."
                trace.append(
                    {
                        "title": "Key matches",
                        "text": (
                            f"Stored key {item[0]!r} equals search key {key!r}.\n\n"
                            f"{action}"
                        ),
                        "bucket": index,
                    }
                )
                self._render_buckets()
                self._attach_table_history(
                    trace,
                    initial_state,
                    self._snapshot_table() if delete else None,
                )
                return trace, result
            trace.append(
                {
                    "title": "Different key; continue probing",
                    "text": (
                        f"This slot contains key {item[0]!r}, not {key!r}.\n\n"
                        "Calculate the next index with the same double-hash formula."
                    ),
                    "bucket": index,
                }
            )
        self._render_buckets()
        self._attach_table_history(trace, initial_state)
        return trace, f"Key {key!r} was not found."

    def load_demo(self):
        self.buckets = [None for _ in range(BUCKET_COUNT)]
        self.item_count = 0
        self.visual_buckets = None
        empty_state = self._snapshot_table()
        seen = {}
        collision = None
        for first in "abcdefghijklmnopqrstuvwxyz":
            for second in "abcdefghijklmnopqrstuvwxyz":
                key = first + second
                bucket = self._hash_value(key, HASH_PRIME_1)
                if bucket in seen:
                    collision = (bucket, seen[bucket], key)
                    break
                seen[bucket] = key
            if collision:
                break
        _initial_bucket, first_key, second_key = collision
        trace_first, _ = self._insert_item(first_key, "first value")
        trace_second, _ = self._insert_item(second_key, "second value")
        trace_update, _ = self._insert_item(first_key, "updated value")
        trace_delete, _ = self._find_item(first_key, delete=True)
        trace_search, result = self._find_item(second_key, delete=False)
        self.message_var.set(second_key)
        self.value_var.set("second value")
        summary = [
            {
                "title": "Demo: same starting hash",
                "text": (
                    f"Different keys {first_key!r} and {second_key!r} both start at "
                    f"slot {_initial_bucket}.\n\n"
                    "The second key probes to another slot; it does not form a chain."
                ),
                "bucket": _initial_bucket,
                "table_state": empty_state,
            }
        ]
        self._set_trace(
            summary + trace_first + trace_second + trace_update + trace_delete + trace_search,
            f"Demo: collision, same-key update, tombstone, then search. {result}",
        )

    def clear_table(self):
        self.buckets = [None for _ in range(BUCKET_COUNT)]
        self.item_count = 0
        self.visual_buckets = None
        self.active_bucket = None
        self._render_buckets()
        self._set_trace([], "Table cleared.")


def main():
    root = tk.Tk()
    HashTableTeacher(root)
    root.mainloop()


if __name__ == "__main__":
    main()