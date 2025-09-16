# Privacy

ColdWatch stores accessibility events and text snapshots locally in SQLite.

## Defaults
- Text content is captured by default when the logger observes text-accessible widgets.
- Metadata (app name, role, bounds, states) is always captured to maintain an object registry.

## Disabling text capture
Run the logger with `--no-text` to store metadata only. Text content will be suppressed, although hashes are retained to detect changes.

```sh
coldwatch run --no-text
```

## Storage location
By default the database resides in the current working directory as `accessibility_log.db`. Override with `--db /path/to/db.sqlite`.

## Recommendations
- Store databases on encrypted volumes when handling sensitive data.
- Rotate databases periodically and remove old snapshots if no longer required.
- Keep the ColdWatch repository and artifacts under user-only permissions.
