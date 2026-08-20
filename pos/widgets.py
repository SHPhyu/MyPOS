"""Reusable CustomTkinter widgets shared across views."""
import tkinter as tk

import customtkinter as ctk

from . import theme

# Rendering more rows than this as real widgets is what made Sales History
# freeze the whole app with a large database (691 rows took ~26s to build
# as CTk widgets). Past this cap we show only the most recent rows and a
# hint to narrow the filter/search instead of paying that cost every time.
MAX_RENDERED_ROWS = 150


class DataTable(ctk.CTkFrame):
    """A scrollable, selectable list with column headers — the CTk stand-in
    for ttk.Treeview, styled to look like modern app rows instead of a
    spreadsheet grid.

    Row cells are built with plain tkinter widgets (not CTk ones) on
    purpose: CTkLabel/CTkFrame do custom canvas drawing for rounded
    corners and are individually much more expensive to construct, which
    matters a lot once a table has hundreds of rows.
    """

    def __init__(self, master, columns, on_select=None, on_double_click=None,
                 height=300, empty_text="ရလဒ်မရှိပါ", **kwargs):
        super().__init__(master, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS, **kwargs)
        self.columns = columns
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.empty_text = empty_text
        self.rows_data = []
        self.row_widgets = []  # list of (frame, tag)
        self.selected_index = None
        self._truncated_notice = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=theme.ROW_ALT, corner_radius=theme.RADIUS)
        header.grid(row=0, column=0, sticky="ew", padx=1, pady=(1, 0))
        for i, col in enumerate(columns):
            lbl = ctk.CTkLabel(
                header, text=col["heading"], width=col.get("width", 100),
                anchor=col.get("anchor", "w"), font=theme.font(12, "bold"),
                text_color=theme.TEXT_MUTED,
            )
            lbl.pack(side="left", padx=(14 if i == 0 else 4, 4), pady=8)

        self.body = ctk.CTkScrollableFrame(self, fg_color=theme.BG_CARD, corner_radius=0, height=height)
        self.body.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))

        self.empty_label = ctk.CTkLabel(self.body, text=empty_text, text_color=theme.TEXT_MUTED, font=theme.font(12))

    def _row_bg(self, index, tag):
        if tag == "warn":
            return theme.ROW_WARN
        return theme.BG_CARD if index % 2 == 0 else theme.ROW_ALT

    def set_rows(self, rows, row_tag=None):
        """rows: iterable of dict-like objects (dict or sqlite3.Row).
        row_tag(row) -> "warn" to tint a row, or None.
        """
        for frame, _tag in self.row_widgets:
            frame.destroy()
        self.row_widgets = []
        if self._truncated_notice is not None:
            self._truncated_notice.destroy()
            self._truncated_notice = None
        all_rows = list(rows)
        self.rows_data = all_rows[:MAX_RENDERED_ROWS]
        self.selected_index = None
        self.empty_label.pack_forget()

        if not all_rows:
            self.empty_label.pack(pady=24)
            return

        row_height = 34

        for idx, row in enumerate(self.rows_data):
            tag = row_tag(row) if row_tag else None
            bg = self._row_bg(idx, tag)
            row_frame = tk.Frame(self.body, bg=bg, height=row_height)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)
            widgets = [row_frame]
            for i, col in enumerate(self.columns):
                try:
                    value = row[col["key"]]
                except (KeyError, IndexError):
                    value = ""
                fmt = col.get("format")
                text = fmt(value) if fmt else ("" if value is None else str(value))
                anchor = col.get("anchor", "w")
                # Fixed-pixel-width cell frame keeps columns aligned with the
                # (pixel-width) CTkLabel header, while the cheap tk.Label
                # inside is what keeps row construction fast at scale.
                cell = tk.Frame(row_frame, bg=bg, width=col.get("width", 100))
                cell.pack(side="left", fill="y", padx=(14 if i == 0 else 4, 4))
                cell.pack_propagate(False)
                lbl = tk.Label(cell, text=text, anchor=anchor, font=theme.font(12), fg=theme.TEXT_DARK, bg=bg)
                lbl.pack(fill="both", expand=True, pady=8)
                widgets.extend([cell, lbl])

            for w in widgets:
                w.bind("<Button-1>", lambda e, i=idx: self._select(i))
                w.bind("<Double-Button-1>", lambda e, i=idx: self._double_click(i))

            self.row_widgets.append((row_frame, tag))

        if len(all_rows) > MAX_RENDERED_ROWS:
            self._truncated_notice = tk.Label(
                self.body,
                text=f"{len(all_rows):,} ခုအနက် ပထမ {MAX_RENDERED_ROWS} ခုသာ ပြထားပါသည် — ရှာဖွေခြင်း/ရက်စွဲစစ်ထုတ်ခြင်းဖြင့် ကျဉ်းအောင်ပြုလုပ်ပါ",
                font=theme.font(11), fg=theme.TEXT_MUTED, bg=theme.BG_CARD, wraplength=500, justify="left",
            )
            self._truncated_notice.pack(fill="x", pady=12, padx=10)

    def _paint_row(self, index, bg):
        frame, _tag = self.row_widgets[index]
        frame.configure(bg=bg)
        for cell in frame.winfo_children():
            cell.configure(bg=bg)
            for label in cell.winfo_children():
                label.configure(bg=bg)

    def _select(self, index):
        if self.selected_index is not None and self.selected_index < len(self.row_widgets):
            prev_frame, prev_tag = self.row_widgets[self.selected_index]
            self._paint_row(self.selected_index, self._row_bg(self.selected_index, prev_tag))
        self.selected_index = index
        self._paint_row(index, theme.ROW_SELECTED)
        if self.on_select:
            self.on_select(self.rows_data[index])

    def _double_click(self, index):
        self._select(index)
        if self.on_double_click:
            self.on_double_click(self.rows_data[index])

    def get_selected(self):
        if self.selected_index is None:
            return None
        return self.rows_data[self.selected_index]

    def clear_selection(self):
        if self.selected_index is not None and self.selected_index < len(self.row_widgets):
            prev_frame, prev_tag = self.row_widgets[self.selected_index]
            self._paint_row(self.selected_index, self._row_bg(self.selected_index, prev_tag))
        self.selected_index = None


class SectionHeading(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text, font=theme.font(18, "bold"), text_color=theme.TEXT_DARK, **kwargs)
