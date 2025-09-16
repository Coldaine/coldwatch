# Troubleshooting

## AT-SPI not available
- Ensure you are logged into a graphical Linux session.
- Verify the `AT_SPI_BUS_ADDRESS` environment variable is set (it typically is when a session is active).
- When running headless, set `XDG_RUNTIME_DIR=/run/user/$(id -u)` and launch via `dbus-run-session`.

## pyatspi import errors
Install system packages that provide the bindings:
```sh
sudo apt install python3-pyatspi python3-gi gir1.2-gtk-3.0
```

## No events captured under Xvfb
- Ensure the logger and test app share the same dbus session (`dbus-run-session` wrapper).
- Start `accerciser` briefly before running to warm the accessibility bus.

## Database locked
- Avoid running multiple loggers targeting the same database.
- Use `--db` to isolate runs in separate files.
