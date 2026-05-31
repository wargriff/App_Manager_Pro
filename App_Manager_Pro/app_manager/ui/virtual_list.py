# virtual_list.py — liste virtualisée à défilement fluide

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional


class VirtualList:

    ROW_HEIGHT = 58
    POOL_SIZE = 36
    SCROLL_END_MS = 120

    def __init__(
        self,
        parent: tk.Widget,
        build_row: Callable[[tk.Frame], dict],
        on_scroll_end: Optional[Callable[[], None]] = None,
    ):

        self.parent = parent
        self.build_row = build_row
        self.on_scroll_end = on_scroll_end

        self.items: list[Any] = []
        self._rows: list[dict] = []
        self._render_start = -1
        self._row_keys: list[Optional[tuple]] = []
        self._scrolling = False
        self._scroll_timer: Optional[str] = None
        self._path_exists: dict[str, bool] = {}

        self.canvas = tk.Canvas(
            parent,
            bg="#121212",
            highlightthickness=0,
            yscrollincrement=1,
        )

        self.scrollbar = tk.Scrollbar(
            parent,
            orient="vertical",
            command=self.canvas.yview,
        )

        self.canvas.configure(yscrollcommand=self._on_scrollbar)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.container = tk.Frame(self.canvas, bg="#121212")
        self._window_id = self.canvas.create_window(
            (0, 0),
            window=self.container,
            anchor="nw",
        )

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

        for _ in range(self.POOL_SIZE):
            frame = tk.Frame(
                self.container,
                bg="#1e1e1e",
                height=self.ROW_HEIGHT - 2,
            )
            frame.pack_propagate(False)
            row = self.build_row(frame)
            row["frame"] = frame
            row["frame"].place_forget()
            self._rows.append(row)
            self._row_keys.append(None)

    # =====================================================
    # DATA
    # =====================================================

    def set_items(self, items: list[Any]):

        self.items = items
        self._render_start = -1
        self._update_scrollregion()
        self.render(force=True)

    def item_key(self, item) -> tuple:

        return (
            getattr(item, "name", "").lower(),
            (getattr(item, "path", None) or "").lower(),
        )

    def path_exists(self, path: str) -> bool:

        if not path:
            return False

        if path not in self._path_exists:
            import os
            self._path_exists[path] = os.path.exists(path)

        return self._path_exists[path]

    def clear_cache(self):

        self._path_exists.clear()
        self._render_start = -1

    # =====================================================
    # SCROLL
    # =====================================================

    def _bind_wheel(self, _event=None):

        self.canvas.bind_all("<MouseWheel>", self._on_wheel, add="+")

    def _unbind_wheel(self, _event=None):

        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):

        if not self.items:
            return

        step = -event.delta / 120 * (self.ROW_HEIGHT * 2)
        top = self.canvas.canvasy(0)
        total = max(len(self.items) * self.ROW_HEIGHT, 1)
        new_top = max(0, min(top + step, total - 1))

        self.canvas.yview_moveto(new_top / total)
        self._scrolling = True
        self.render(force=True)

        if self._scroll_timer:
            self.canvas.after_cancel(self._scroll_timer)

        self._scroll_timer = self.canvas.after(
            self.SCROLL_END_MS,
            self._end_scroll,
        )

    def _end_scroll(self):

        self._scroll_timer = None
        self._scrolling = False
        self._render_start = -1
        self.render(force=True)

        if self.on_scroll_end:
            self.on_scroll_end()

    def _on_scrollbar(self, first: str, last: str):

        self.scrollbar.set(first, last)
        self.render(force=True)

    def _on_resize(self, event):

        self.canvas.itemconfigure(self._window_id, width=event.width)
        self._render_start = -1
        self.render(force=True)

    def _update_scrollregion(self):

        width = max(self.canvas.winfo_width(), 300)
        height = max(len(self.items) * self.ROW_HEIGHT, 1)

        self.canvas.configure(scrollregion=(0, 0, width, height))
        self.container.configure(width=width, height=height)

    def scroll_to_top(self):

        self.canvas.yview_moveto(0)
        self._render_start = -1
        self.render(force=True)

    @property
    def is_scrolling(self) -> bool:

        return self._scrolling

    # =====================================================
    # RENDER
    # =====================================================

    def render(self, force: bool = False):

        if not self.items:
            for row in self._rows:
                row["frame"].place_forget()
            return

        width = max(self.canvas.winfo_width(), 300)
        scroll_y = self.canvas.canvasy(0)
        start = max(0, int(scroll_y // self.ROW_HEIGHT))

        if not force and start == self._render_start:
            return

        self._render_start = start
        visible = self.items[start:start + len(self._rows)]
        item_width = max(width - 24, 200)

        for index, row in enumerate(self._rows):

            if index >= len(visible):
                row["frame"].place_forget()
                self._row_keys[index] = None
                continue

            item = visible[index]
            key = self.item_key(item)
            y = (start + index) * self.ROW_HEIGHT

            row["frame"].place(
                x=8,
                y=y + 1,
                width=item_width,
                height=self.ROW_HEIGHT - 2,
            )

            if self._row_keys[index] != key:
                self._row_keys[index] = key
                row["bind"](item, self.is_scrolling)

        self._update_scrollregion()

    def destroy(self):

        try:
            self._unbind_wheel()
        except Exception:
            pass

        if self._scroll_timer:
            try:
                self.canvas.after_cancel(self._scroll_timer)
            except Exception:
                pass
