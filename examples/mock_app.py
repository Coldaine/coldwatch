#!/usr/bin/env python3
"""Small GTK demo app that mutates text to exercise the logger."""

import threading
import time

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402


class MockApp:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="ColdWatch Mock App")
        self.window.connect("destroy", Gtk.main_quit)

        self.textview = Gtk.TextView()
        self.buffer = self.textview.get_buffer()
        self.window.add(self.textview)
        self.window.show_all()

        self.window.get_accessible().set_name("ColdWatchMockWindow")
        self.textview.get_accessible().set_name("ColdWatchMockTextView")

    def run_script(self) -> None:
        time.sleep(1)
        GLib.idle_add(self.buffer.set_text, "Hello, ColdWatch!", -1)
        time.sleep(1)
        GLib.idle_add(self.buffer.insert_at_cursor, " Logging test.", -1)
        time.sleep(1)
        GLib.idle_add(self.buffer.set_text, "", -1)
        time.sleep(1)
        GLib.idle_add(self.buffer.set_text, "Final line.", -1)
        time.sleep(1)
        GLib.idle_add(Gtk.main_quit)


def main() -> None:
    app = MockApp()
    worker = threading.Thread(target=app.run_script, daemon=True)
    worker.start()
    Gtk.main()


if __name__ == "__main__":
    main()
