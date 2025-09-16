from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

from . import db
from .types import RunConfig

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    pass


@dataclass
class ScannerState:
    text_hashes: dict[str, str] = field(default_factory=dict)
    focused_objects: set[str] = field(default_factory=set)


def wait_for_registry(timeout: float, poll_interval: float = 0.5) -> bool:
    import pyatspi

    start = time.time()
    while True:
        try:
            pyatspi.Registry.getDesktop(0)
            return True
        except Exception:
            if time.time() - start >= timeout:
                return False
            time.sleep(poll_interval)


def walk_tree(conn: Any, cfg: RunConfig, state: ScannerState) -> None:
    import pyatspi

    desktop = pyatspi.Registry.getDesktop(0)
    for index in range(desktop.childCount):
        app = desktop.getChildAtIndex(index)
        if not _should_process_app(app, cfg):
            continue
        _scan_widget(app, conn, cfg, state, depth=0)


def subscribe_events(conn: Any, cfg: RunConfig, state: ScannerState) -> None:
    import pyatspi

    stop_event = threading.Event()

    def _on_text_changed(event: Any) -> None:
        _handle_event(conn, cfg, state, event)
        _capture_if_allowed(conn, cfg, state, event.source)

    def _on_focus_changed(event: Any) -> None:
        _handle_event(conn, cfg, state, event)
        source = event.source
        if source is None:
            return
        object_id = _object_id(source)
        if event.detail1:
            state.focused_objects.add(object_id)
            _capture_if_allowed(conn, cfg, state, source)
        else:
            state.focused_objects.discard(object_id)

    def _on_children_changed(event: Any) -> None:
        _handle_event(conn, cfg, state, event)

    pyatspi.Registry.registerEventListener(_on_text_changed, "object:text-changed")
    pyatspi.Registry.registerEventListener(
        _on_focus_changed, "object:state-changed:focused"
    )
    pyatspi.Registry.registerEventListener(
        _on_children_changed, "object:children-changed"
    )

    def _periodic_scan() -> None:
        while not stop_event.wait(max(cfg.interval, 1.0)):
            try:
                walk_tree(conn, cfg, state)
            except Exception:
                logger.exception("Periodic scan failed")

    scan_thread = threading.Thread(target=_periodic_scan, daemon=True)
    scan_thread.start()

    logger.info("✅ Event listeners registered. Press Ctrl+C to stop.")

    try:
        pyatspi.Registry.start()
    finally:
        stop_event.set()
        pyatspi.Registry.deregisterEventListener(
            _on_text_changed, "object:text-changed"
        )
        pyatspi.Registry.deregisterEventListener(
            _on_focus_changed, "object:state-changed:focused"
        )
        pyatspi.Registry.deregisterEventListener(
            _on_children_changed, "object:children-changed"
        )
        logger.info("🛑 Event loop stopped")


def _handle_event(conn: Any, cfg: RunConfig, state: ScannerState, event: Any) -> None:
    source = event.source
    if source is None or not _should_process_source(source, cfg):
        return

    timestamp = db.utcnow()
    object_id = _object_id(source)
    info = _object_info(source)
    record = db.EventRecord(
        timestamp=timestamp,
        event_type=event.type,
        app_name=info.get("app_name"),
        object_id=object_id,
        object_role=info.get("role"),
        object_name=info.get("name"),
        detail1=int(event.detail1) if event.detail1 is not None else None,
        detail2=int(event.detail2) if event.detail2 is not None else None,
        source_info={
            "path": info.get("path"),
            "interfaces": info.get("interfaces"),
            "states": info.get("states"),
        },
    )
    db.log_event(conn, record)


def _capture_if_allowed(
    conn: Any, cfg: RunConfig, state: ScannerState, source: Any
) -> None:
    if source is None or not _should_process_source(source, cfg):
        return

    info = _object_info(source)
    if not info.get("is_text_widget"):
        return

    text_content = info.get("text_content", "")
    text_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
    object_id = info["object_id"]

    if state.text_hashes.get(object_id) == text_hash:
        return

    state.text_hashes[object_id] = text_hash
    timestamp = db.utcnow()

    snapshot = db.SnapshotRecord(
        timestamp=timestamp,
        object_id=object_id,
        app_name=info.get("app_name"),
        object_role=info.get("role"),
        object_name=info.get("name"),
        text_content=text_content if cfg.capture_text else "",
        text_hash=text_hash,
        char_count=len(text_content),
        can_read=info.get("can_read", False),
        can_write=info.get("can_write", False),
        interfaces=info.get("interfaces", []),
        states=info.get("states", []),
        bounds=info.get("bounds"),
    )

    if cfg.capture_text:
        stored = db.store_snapshot(conn, snapshot)
        if stored:
            logger.success(
                "📄 Captured text (%s chars) from %s | %s",
                snapshot.char_count,
                snapshot.app_name,
                snapshot.object_role,
            )
    registry = db.RegistryRecord(
        object_id=object_id,
        app_name=info.get("app_name"),
        object_role=info.get("role"),
        object_name=info.get("name"),
        last_seen=timestamp,
        is_text_widget=True,
        interfaces=info.get("interfaces", []),
        states=info.get("states", []),
        bounds=info.get("bounds"),
        last_text_hash=text_hash,
    )
    db.update_registry(conn, registry)


def _scan_widget(
    widget: Any,
    conn: Any,
    cfg: RunConfig,
    state: ScannerState,
    *,
    depth: int,
    max_depth: int = 25,
) -> None:
    if depth > max_depth:
        return

    if _should_process_source(widget, cfg):
        _capture_if_allowed(conn, cfg, state, widget)

    for child_index in range(getattr(widget, "childCount", 0)):
        try:
            child = widget.getChildAtIndex(child_index)
        except Exception:
            continue
        _scan_widget(child, conn, cfg, state, depth=depth + 1, max_depth=max_depth)


def _should_process_app(obj: Any, cfg: RunConfig) -> bool:
    name = _safe_name(obj)
    return _matches_app_filters(name, cfg)


def _should_process_source(obj: Any, cfg: RunConfig) -> bool:
    if obj is None:
        return False
    app = obj.getApplication() if hasattr(obj, "getApplication") else None
    app_name = _safe_name(app)
    role = _safe_role(obj)
    return _matches_app_filters(app_name, cfg) and _matches_role_filters(role, cfg)


def _matches_app_filters(name: str | None, cfg: RunConfig) -> bool:
    if name is None:
        name = "unknown"
    lowered = name.lower()
    if cfg.include_apps:
        return lowered in {app.lower() for app in cfg.include_apps}
    if cfg.exclude_apps and lowered in {app.lower() for app in cfg.exclude_apps}:
        return False
    return True


def _matches_role_filters(role: str | None, cfg: RunConfig) -> bool:
    if role is None:
        return False
    if cfg.include_roles:
        return role in cfg.include_roles
    if cfg.exclude_roles and role in cfg.exclude_roles:
        return False
    return True


def _object_id(obj: Any) -> str:
    try:
        app = obj.getApplication()
        app_name = _safe_name(app) or "unknown"
        role_name = _safe_role(obj) or "unknown"
        path = getattr(obj, "path", None)
        if path:
            identifier = str(path)
        else:
            identifier = hex(id(obj))
        return f"{app_name}:{role_name}:{identifier}"
    except Exception:
        return f"unknown:{hex(id(obj))}"


def _object_info(obj: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "object_id": _object_id(obj),
        "app_name": _safe_name(
            obj.getApplication() if hasattr(obj, "getApplication") else None
        ),
        "role": _safe_role(obj),
        "name": _safe_name(obj),
        "path": str(getattr(obj, "path", "")) or None,
        "interfaces": _safe_interfaces(obj),
        "states": _safe_states(obj),
        "bounds": _safe_bounds(obj),
        "is_text_widget": _is_text_widget(obj),
    }

    text_content, can_read, can_write = _extract_text(obj)
    info["text_content"] = text_content
    info["can_read"] = can_read
    info["can_write"] = can_write
    return info


def _extract_text(obj: Any) -> tuple[str, bool, bool]:
    try:
        text_iface = obj.queryText()
    except Exception:
        return "", False, _state_editable(obj)

    try:
        character_count = text_iface.characterCount
        content = text_iface.getText(0, character_count)
        return content or "", True, _state_editable(obj)
    except Exception:
        return "", False, _state_editable(obj)


def _state_editable(obj: Any) -> bool:
    try:
        states = obj.getState()
        if hasattr(states, "contains"):
            from pyatspi import STATE_EDITABLE  # type: ignore

            return bool(states.contains(STATE_EDITABLE))
    except Exception:
        return False
    return False


def _safe_name(obj: Any) -> str | None:
    try:
        if obj is None:
            return None
        name = getattr(obj, "name", None)
        if name:
            return str(name)
    except Exception:
        return None
    return None


def _safe_role(obj: Any) -> str | None:
    try:
        role = obj.getRoleName() if hasattr(obj, "getRoleName") else None
        if role:
            return str(role)
    except Exception:
        return None
    return None


def _safe_interfaces(obj: Any) -> list[str]:
    try:
        interfaces = obj.getInterfaces() if hasattr(obj, "getInterfaces") else []
        return [str(interface) for interface in interfaces]
    except Exception:
        return []


def _safe_states(obj: Any) -> list[str]:
    try:
        state_set = obj.getState() if hasattr(obj, "getState") else None
        if state_set and hasattr(state_set, "getStates"):
            return [str(state) for state in state_set.getStates()]
    except Exception:
        return []
    return []


def _safe_bounds(obj: Any) -> dict[str, int] | None:
    try:
        if not hasattr(obj, "queryComponent"):
            return None
        component = obj.queryComponent()
        from pyatspi import DESKTOP_COORDS  # type: ignore

        x, y = component.getPosition(DESKTOP_COORDS)
        width, height = component.getSize()
        return {"x": int(x), "y": int(y), "width": int(width), "height": int(height)}
    except Exception:
        return None


def _is_text_widget(obj: Any) -> bool:
    try:
        obj.queryText()
        return True
    except Exception:
        return False
