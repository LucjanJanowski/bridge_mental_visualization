#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bridge Temporary Evaluation – Equalized Layout
- Three rows with equal height (uniform grid rows)
- N (top) and S (bottom) centered horizontally and the SAME width/height as W/E columns
- Inline cards rendered as Label "buttons" with full solid color fill on toggle
- Enter/Tab jumps to next suit; auto-mark when replacing a single 'X' with one rank
- Per-player Cards counter (total across suits)
- Center "table" square with N/E/S/W tiles toggling green <-> red on click
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from collections import Counter, defaultdict

RANKS_ORDER = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2', 'X']
RANK_VALUES = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
SUITS = [('S', '♠'), ('H', '♥'), ('D', '♦'), ('C', '♣')]

def normalize_cards(text):
    if text is None:
        return ""
    raw = text.strip().upper().replace(',', ' ').replace('-', ' ').replace('.', ' ')
    raw = raw.replace('10', 'T')
    parts = [p for p in raw.split() if p]
    tokens = list(parts[0]) if len(parts) == 1 else [ch for p in parts for ch in p]
    tokens = ['T' if t == '0' else t for t in tokens]
    tokens = [t for t in tokens if t in RANKS_ORDER]
    tokens_sorted = sorted(tokens, key=lambda t: RANKS_ORDER.index(t))
    return ''.join(tokens_sorted)

def hcp_from_cards(cards):
    return sum(RANK_VALUES.get(ch, 0) for ch in cards)

class HandFrame(ttk.LabelFrame):
    def __init__(self, master, player_label, on_change=None, *args, **kwargs):
        super().__init__(master, text=f" {player_label} ", padding=(6, 4), *args, **kwargs)
        self.on_change = on_change

        self.last_cards = {sc: "" for sc, _ in SUITS}
        self.played_counts = {sc: defaultdict(int) for sc, _ in SUITS}
        self.card_strips = {}
        self.cards_entries = {}

        row = 0
        ttk.Label(self, text="Pts").grid(row=row, column=0, sticky="w", padx=(0,4))
        self.points_min = ttk.Entry(self, width=3, justify='center')
        ttk.Label(self, text="–").grid(row=row, column=2, sticky="w")
        self.points_max = ttk.Entry(self, width=3, justify='center')
        self.points_min.grid(row=row, column=1, sticky="w")
        self.points_max.grid(row=row, column=3, sticky="w", padx=(0,6))
        row += 1

        # HCP + Cards counters
        ttk.Label(self, text="HCP").grid(row=row, column=0, sticky="w", pady=(2, 2))
        self.hcp_var = tk.StringVar(value="0")
        ttk.Label(self, textvariable=self.hcp_var, width=4).grid(row=row, column=1, sticky="w", pady=(2, 2))

        ttk.Label(self, text="Cards").grid(row=row, column=2, sticky="e", pady=(2, 2))
        self.cards_total_var = tk.StringVar(value="0")
        ttk.Label(self, textvariable=self.cards_total_var, width=4).grid(row=row, column=3, sticky="w", pady=(2, 2))
        row += 1

        self.suit_count_vars = {}
        self.suit_card_vars = {}

        # Columns: 0 Suit, 1 Count, 2 Entry (fixed), 3 Strip (expands)
        for suit_index, (suit_code, suit_sym) in enumerate(SUITS):
            ttk.Label(self, text=f"{suit_sym}").grid(row=row, column=0, sticky="w")
            cnt_var = tk.StringVar()
            self.suit_count_vars[suit_code] = cnt_var
            cnt_entry = ttk.Entry(self, width=3, textvariable=cnt_var, justify='center')
            cnt_entry.grid(row=row, column=1, sticky="w", padx=(0, 6))

            cards_var = tk.StringVar()
            self.suit_card_vars[suit_code] = cards_var
            cards_entry = ttk.Entry(self, width=13, textvariable=cards_var)
            cards_entry.grid(row=row, column=2, sticky="w")
            self.cards_entries[suit_code] = cards_entry

            strip = ttk.Frame(self)
            strip.grid(row=row, column=3, sticky="we", padx=(6,0))
            self.card_strips[suit_code] = strip

            def on_cards_change(evt=None, sc=suit_code, var=cards_var, cntv=cnt_var):
                old = self.last_cards[sc]
                new_norm = normalize_cards(var.get())
                if new_norm != var.get().upper():
                    var.set(new_norm)
                cntv.set(str(len(new_norm)))
                self.update_stats()

                # auto-mark a single new rank that replaced one 'X'
                old_norm = normalize_cards(old)
                if old_norm:
                    old_counter = Counter(old_norm)
                    new_counter = Counter(new_norm)
                    delta_x = old_counter.get('X', 0) - new_counter.get('X', 0)
                    added = {r: new_counter[r] - old_counter.get(r, 0) for r in new_counter if r != 'X'}
                    added = {r: c for r, c in added.items() if c > 0}
                    if delta_x == 1 and sum(added.values()) == 1:
                        added_rank = next(iter(added.keys()))
                        self.played_counts[sc][added_rank] += 1

                self.last_cards[sc] = new_norm
                self.rebuild_card_strip(sc)

                if evt and str(evt.keysym) in ("Return", "Tab"):
                    self.focus_next_suit(sc)
                    return "break"

            cards_entry.bind("<FocusOut>", on_cards_change)
            cards_entry.bind("<Return>", on_cards_change)
            cards_entry.bind("<Tab>", on_cards_change)

            def on_count_change(*args, sc=suit_code, var=cards_var, entry=cards_entry):
                try:
                    desired = int(self.suit_count_vars[sc].get())
                except Exception:
                    return
                cards = var.get()
                # ttk.Entry background may be theme-controlled, but try:
                try:
                    entry.config(background="#fff4f4" if len(cards) != desired else "white")
                except tk.TclError:
                    pass

            cnt_var.trace_add("write", on_count_change)

            self.rebuild_card_strip(suit_code)
            row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=4, sticky="we", pady=(6, 0))
        ttk.Button(btns, text="Sort & Sync", command=self.sort_all).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.clear_all).pack(side="left", padx=(6,0))

        # Column stretch: only the card strip expands
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)

    def focus_next_suit(self, current_suit_code):
        order = ['S', 'H', 'D', 'C']
        try:
            idx = order.index(current_suit_code)
            next_suit = order[(idx + 1) % len(order)]
            self.cards_entries[next_suit].focus_set()
            self.cards_entries[next_suit].icursor('end')
        except Exception:
            pass

    # Label-based "buttons" with full solid color
    def rebuild_card_strip(self, suit_code):
        strip = self.card_strips[suit_code]
        for w in strip.winfo_children():
            w.destroy()
        cards = self.suit_card_vars[suit_code].get()
        played_counts = self.played_counts[suit_code]
        used_played = Counter()

        for rank in cards:
            is_played = False
            if rank != 'X' and used_played[rank] < played_counts.get(rank, 0):
                is_played = True
                used_played[rank] += 1

            lbl = tk.Label(
                strip,
                text=rank,
                width=2,
                height=1,
                font=("TkDefaultFont", 10, "bold"),
                bd=1,
                relief="solid",
                fg="#000000",
                bg="#6fff6f" if is_played else "#ffffff",
            )
            lbl._played = is_played

            def on_toggle(e=None, l=lbl, r=rank):
                if r == 'X':
                    return
                l._played = not getattr(l, "_played", False)
                if l._played:
                    l.configure(bg="#6fff6f", fg="#000000")
                    self.played_counts[suit_code][r] = self.played_counts[suit_code].get(r, 0) + 1
                else:
                    l.configure(bg="#ffffff", fg="#000000")
                    if self.played_counts[suit_code].get(r, 0) > 0:
                        self.played_counts[suit_code][r] -= 1

            lbl.bind("<Button-1>", on_toggle)
            lbl.pack(side="left", padx=1, pady=1, ipadx=4, ipady=2)

    def sort_all(self):
        for sc, var in self.suit_card_vars.items():
            norm = normalize_cards(var.get())
            var.set(norm)
            self.suit_count_vars[sc].set(str(len(norm)))
            self.last_cards[sc] = norm
            self.rebuild_card_strip(sc)
        self.update_stats()

    def clear_all(self):
        self.points_min.delete(0, 'end')
        self.points_max.delete(0, 'end')
        for sc in list(self.suit_card_vars.keys()):
            self.suit_card_vars[sc].set("")
            self.suit_count_vars[sc].set("")
            self.last_cards[sc] = ""
            self.played_counts[sc].clear()
            self.rebuild_card_strip(sc)
        self.update_stats()

    def update_stats(self):
        total_hcp = 0
        total_cards = 0
        for sc, var in self.suit_card_vars.items():
            cards = var.get()
            total_hcp += hcp_from_cards(cards)
            total_cards += len(cards)
        self.hcp_var.set(str(total_hcp))
        self.cards_total_var.set(str(total_cards))
        if callable(self.on_change):
            self.on_change()

    def get_state(self):
        suits = {}
        for sc in self.suit_card_vars:
            suits[sc] = {
                'count': self.suit_count_vars[sc].get(),
                'cards': self.suit_card_vars[sc].get(),
                'played': dict(self.played_counts[sc]),
            }
        return {
            'player': self.player_label,
            'points_range': (self.points_min.get(), self.points_max.get()),
            'hcp': self.hcp_var.get(),
            'cards_total': self.cards_total_var.get(),
            'suits': suits
        }

class BridgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bridge Temporary Evaluation – Equalized Layout")
        self.geometry("980x700")
        self.minsize(820, 560)

        # Fonts
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        tkfont.nametofont("TkTextFont").configure(size=12)
        tkfont.nametofont("TkFixedFont").configure(size=12)

        # Top bar
        topbar = ttk.Frame(self, padding=(6,6))
        topbar.pack(side="top", fill="x")
        ttk.Label(topbar, text="Bridge Temporary Evaluation", font=("TkDefaultFont", 13, "bold")).pack(side="left")
        ttk.Button(topbar, text="Validate All", command=self.validate_all).pack(side="right", padx=(6,0))
        ttk.Button(topbar, text="Dump State to Console", command=self.dump_state).pack(side="right", padx=(6,0))
        ttk.Button(topbar, text="Sort & Sync All", command=self.sort_all_hands).pack(side="right", padx=(6,0))
        ttk.Button(topbar, text="Clear All", command=self.clear_all_hands).pack(side="right")

        # Summary bar just under the buttons
        self.summary_var = tk.StringVar(value="Total cards: 0 | ♠0 ♥0 ♦0 ♣0 | Min pts: 0 | Max pts: 0")
        summary = ttk.Frame(self, padding=(6, 3))
        summary.pack(side="top", fill="x")
        ttk.Label(summary, textvariable=self.summary_var).pack(side="left")

        # Main grid frame
        grid = ttk.Frame(self, padding=4)
        grid.pack(side="top", fill="both", expand=True)
        self.grid_frame = grid

        # --- Column/row layout: 0 = W, 1 = TABLE (fixed), 2 = E ---
        self.table_size = 140
        self.table_margin = 24  # fixed gap around table (column 1 minsize)

        self.grid_frame.grid_columnconfigure(0, weight=1, uniform="sides")
        self.grid_frame.grid_columnconfigure(1, weight=0, minsize=self.table_size + self.table_margin)  # fixed
        self.grid_frame.grid_columnconfigure(2, weight=1, uniform="sides")
        for r in (0, 1, 2):
            self.grid_frame.grid_rowconfigure(r, weight=1, uniform="rows")

        # Middle row: W/E
        self.frames = {}
        self.frames['W'] = HandFrame(self.grid_frame, 'West', on_change=self.update_global_stats)
        self.frames['E'] = HandFrame(self.grid_frame, 'East', on_change=self.update_global_stats)
        self.frames['W'].grid(row=1, column=0, sticky="nsew", padx=4, pady=0)
        self.frames['E'].grid(row=1, column=2, sticky="nsew", padx=4, pady=0)

        # Top/bottom containers spanning all three columns (N/S centered)
        self.top_container = ttk.Frame(self.grid_frame, padding=0)
        self.bot_container = ttk.Frame(self.grid_frame, padding=0)
        self.top_container.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=4, pady=4)
        self.bot_container.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=4, pady=4)

        for c in (self.top_container, self.bot_container):
            c.grid_columnconfigure(0, weight=1)
            c.grid_columnconfigure(1, weight=0)
            c.grid_columnconfigure(2, weight=1)
            c.grid_rowconfigure(0, weight=1)

        self.frames['N'] = HandFrame(self.top_container, 'North', on_change=self.update_global_stats)
        self.frames['S'] = HandFrame(self.bot_container, 'South', on_change=self.update_global_stats)
        self.frames['N'].grid(row=0, column=1, sticky="nsew")
        self.frames['S'].grid(row=0, column=1, sticky="nsew")

        # Keep N/S the same width as one side column
        self.grid_frame.bind("<Configure>", self._sync_ns_size)
        self.after(0, self._sync_ns_size)

        self.after(100, self._fix_entry_bg)

        # --- CENTER WRAPPER (fixed) + Canvas (placed inside) ---
        self.center_wrap = ttk.Frame(
            self.grid_frame,
            width=self.table_size + self.table_margin,
            height=self.table_size
        )
        self.center_wrap.grid(row=1, column=1, sticky="", pady=0)  # do not stretch
        self.center_wrap.grid_propagate(False)  # lock size

        self.table_canvas = tk.Canvas(
            self.center_wrap,
            width=self.table_size,
            height=self.table_size,
            highlightthickness=0
        )
        # Center horizontally at top of wrapper
        self.table_canvas.place(relx=0.5, rely=0.0, anchor='n')

        # Draw the table tiles
        self.table_colors = {'N': '#6fff6f', 'E': '#6fff6f', 'S': '#6fff6f', 'W': '#6fff6f'}
        self.table_items = {}
        self._draw_table_square()
        self.update_global_stats()

    # ---------- Table square drawing & behavior ----------
    def _draw_table_square(self):
        cv = self.table_canvas
        cv.delete("all")
        size = self.table_size
        pad = 10

        # background square
        cv.create_rectangle(0, 0, size, size, outline="#333333", width=2)

        # positions for letters (middle of each side, inside the border)
        positions = {
            'N': (size / 2, pad + 18),
            'E': (size - (pad + 18), size / 2),
            'S': (size / 2, size - (pad + 18)),
            'W': (pad + 18, size / 2),
        }

        tile_w, tile_h = 34, 26
        for letter, (cx, cy) in positions.items():
            x0, y0 = cx - tile_w / 2, cy - tile_h / 2
            x1, y1 = cx + tile_w / 2, cy + tile_h / 2
            rect = cv.create_rectangle(
                x0, y0, x1, y1,
                fill=self.table_colors[letter],
                outline="#222222", width=1
            )
            text = cv.create_text(cx, cy, text=letter, font=("TkDefaultFont", 12, "bold"))
            cv.tag_bind(rect, "<Button-1>", lambda e, L=letter: self._toggle_table_letter(L))
            cv.tag_bind(text, "<Button-1>", lambda e, L=letter: self._toggle_table_letter(L))
            self.table_items[letter] = (rect, text)

    def _toggle_table_letter(self, letter):
        # decide which pair to toggle together
        pair = ('W', 'E') if letter in ('W', 'E') else ('N', 'S')

        # use the clicked letter's current color to decide the new color
        cur = self.table_colors[letter]
        new_color = "#ff6f6f" if cur == "#6fff6f" else "#6fff6f"

        # apply to both letters in the pair
        for L in pair:
            self.table_colors[L] = new_color
            rect, _ = self.table_items[L]
            self.table_canvas.itemconfig(rect, fill=new_color)

    # ---------- Existing helpers ----------
    def _sync_ns_size(self, event=None):
        """Debounce NS width sync so it runs once after layout settles."""
        if getattr(self, "_sync_pending", False):
            return
        self._sync_pending = True
        # Run once after Tk finishes the current batch of Configure events
        self.after_idle(self._do_sync_ns_size)

    def _do_sync_ns_size(self):
        self._sync_pending = False
        try:
            w = self.frames['W'].winfo_width()
            e = self.frames['E'].winfo_width()
        except tk.TclError:
            # Widgets might be mid-destroy or not yet realized
            return
        col_w = max(w, e)
        if col_w <= 0:
            return
        # Make N/S the same width as a side column
        try:
            self.top_container.grid_columnconfigure(1, minsize=col_w)
            self.bot_container.grid_columnconfigure(1, minsize=col_w)
        except tk.TclError:
            pass

    def _fix_entry_bg(self):
        style = ttk.Style()
        try:
            style.configure("TEntry", fieldbackground="white")
        except Exception:
            pass

    def validate_all(self):
        msgs = []
        for pl in ['N','E','S','W']:
            hf = self.frames[pl]
            total = 0
            for sc in ['S','H','D','C']:
                cnt_str = hf.suit_count_vars[sc].get().strip()
                cards = hf.suit_card_vars[sc].get().strip()
                cnt = int(cnt_str) if cnt_str.isdigit() else None
                if cnt is not None and cnt != len(cards):
                    msgs.append(f"{pl} {sc}: count {cnt} != cards length {len(cards)} ('{cards}')")
                total += len(cards)
            if total and total != 13:
                msgs.append(f"{pl}: has {total} cards (should be 13).")
        if msgs:
            messagebox.showwarning("Validation", "\n".join(msgs))
        else:
            messagebox.showinfo("Validation", "All good!")

    def dump_state(self):
        import json
        state = {pl: self.frames[pl].get_state() for pl in ['N','E','S','W']}
        print(json.dumps(state, indent=2))
        messagebox.showinfo("Dumped", "Current state printed to console.")

    def sort_all_hands(self):
        for hf in self.frames.values():
            hf.sort_all()

    def clear_all_hands(self):
        for hf in self.frames.values():
            hf.clear_all()

    def update_global_stats(self):
        # totals across all four hands
        total_cards = 0
        suit_totals = {'S': 0, 'H': 0, 'D': 0, 'C': 0}
        min_points_sum = 0
        max_points_sum = 0

        for pl in ['N','E','S','W']:
            hf = self.frames.get(pl)
            if not hf:
                continue

            # HCP for this hand
            try:
                hcp = int(hf.hcp_var.get())
            except Exception:
                hcp = 0

            # Pts min/max from entries (blank -> 0)
            def _to_int(entry):
                try:
                    v = entry.get().strip()
                    return int(v) if v else 0
                except Exception:
                    return 0

            pts_min = _to_int(hf.points_min)
            pts_max = _to_int(hf.points_max)

            # suits/cards
            hand_cards = 0
            for sc in ['S','H','D','C']:
                cards = hf.suit_card_vars[sc].get()
                n = len(cards)
                suit_totals[sc] += n
                hand_cards += n
            total_cards += hand_cards

            # min/max points rule: take the higher between HCP and declared min/max
            min_points_sum += max(hcp, pts_min)
            max_points_sum += max(hcp, pts_max)

        # Build summary line
        summary = (
            f"Total cards: {total_cards} | "
            f"♠{suit_totals['S']} ♥{suit_totals['H']} ♦{suit_totals['D']} ♣{suit_totals['C']} | "
            f"Min pts: {min_points_sum} | Max pts: {max_points_sum}"
        )
        self.summary_var.set(summary)


if __name__ == "__main__":
    app = BridgeApp()
    app.mainloop()