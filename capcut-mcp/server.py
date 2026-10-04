"""CapCut MCP server for Windows.

CapCut has no API, so this server edits the project (draft) JSON files on disk.
Approach and hard-won rules adapted from matt-j-penny/capcut-kit:
  * CapCut must be fully closed while a draft is written, or it overwrites the edit.
  * After writing, the Timelines/ cache must be removed, or CapCut ignores the new JSON.
Every edit makes a timestamped backup first.
"""
import copy
import json
import os
import shutil
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DRAFT_ROOT = Path(os.environ.get(
    "CAPCUT_DRAFTS",
    Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
))
BACKUP_ROOT = Path(os.environ.get("CAPCUT_BACKUPS", Path.home() / "capcut-mcp-backups"))
DRAFT_FILES = ("draft_content.json", "draft_info.json")  # name differs between CapCut versions
US = 1_000_000  # CapCut stores time in microseconds

mcp = FastMCP("capcut")


def uid():
    return str(uuid.uuid4()).upper()


def project_dir(name):
    folder = DRAFT_ROOT / name
    if not folder.is_dir():
        raise ValueError(f"No project named {name!r} in {DRAFT_ROOT}")
    return folder


def draft_file(folder):
    for f in DRAFT_FILES:
        if (folder / f).exists():
            return folder / f
    raise ValueError(f"No draft JSON in {folder} (looked for {', '.join(DRAFT_FILES)})")


def capcut_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"],
                         capture_output=True, text=True).stdout
    return "CapCut.exe" in out


def close_capcut(timeout=20):
    if not capcut_running():
        return
    subprocess.run(["taskkill", "/IM", "CapCut.exe"], capture_output=True)
    for _ in range(timeout):
        if not capcut_running():
            return
        time.sleep(1)
    raise RuntimeError("CapCut did not close. Close it manually and try again.")


def backup(folder):
    dest = BACKUP_ROOT / f"{folder.name}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    shutil.copytree(folder, dest)
    return dest


def edit(name, mutate):
    """Close CapCut, back up, load the draft, apply mutate(d), write, clear cache."""
    folder = project_dir(name)
    close_capcut()
    saved = backup(folder)
    path = draft_file(folder)
    d = json.loads(path.read_text(encoding="utf-8"))
    result = mutate(d)
    for t in d["tracks"]:
        for s in t["segments"]:
            if s.get("source_timerange") is None:
                s["source_timerange"] = {"start": 0, "duration": s["target_timerange"]["duration"]}
    d["duration"] = max((s["target_timerange"]["start"] + s["target_timerange"]["duration"]
                         for t in d["tracks"] for s in t["segments"]), default=0)
    text = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    for f in DRAFT_FILES:  # keep both copies in sync when CapCut wrote both
        if (folder / f).exists():
            (folder / f).write_text(text, encoding="utf-8")
    (folder / f"{path.name}.bak").unlink(missing_ok=True)
    shutil.rmtree(folder / "Timelines", ignore_errors=True)
    return f"{result}\nBackup: {saved}\nOpen CapCut to see the change."


def material(d, mid):
    for items in d.get("materials", {}).values():
        if isinstance(items, list):
            for m in items:
                if isinstance(m, dict) and m.get("id") == mid:
                    return m
    return None


def text_of(m):
    try:
        return json.loads(m["content"]).get("text", "")
    except (KeyError, TypeError, ValueError):
        return m.get("content", "") if m else ""


def segments(d, kind):
    return [(t, s) for t in d["tracks"] if t["type"] == kind for s in t["segments"]]


@mcp.tool()
def list_projects() -> str:
    """List all CapCut projects with their last-modified time."""
    if not DRAFT_ROOT.is_dir():
        return f"Drafts folder not found: {DRAFT_ROOT}. Set CAPCUT_DRAFTS to the folder shown in CapCut settings."
    rows = []
    for f in sorted(DRAFT_ROOT.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.is_dir() and any((f / n).exists() for n in DRAFT_FILES):
            rows.append(f"- {f.name}  (modified {datetime.fromtimestamp(f.stat().st_mtime):%Y-%m-%d %H:%M})")
    return "\n".join(rows) or "No projects found."


@mcp.tool()
def read_timeline(project: str) -> str:
    """Summarize a project's timeline: tracks, clips, start/duration in seconds, and text."""
    d = json.loads(draft_file(project_dir(project)).read_text(encoding="utf-8"))
    canvas = d.get("canvas_config", {})
    lines = [f"Project {project}: {d.get('duration', 0) / US:.2f}s, "
             f"{canvas.get('width')}x{canvas.get('height')}, {d.get('fps')} fps"]
    for ti, t in enumerate(d["tracks"]):
        lines.append(f"Track {ti} ({t['type']})")
        for si, s in enumerate(t["segments"]):
            tr, m = s["target_timerange"], material(d, s.get("material_id"))
            label = text_of(m) if t["type"] == "text" else (m or {}).get("material_name") or (m or {}).get("name", "")
            lines.append(f"  [{si}] {tr['start'] / US:.2f}s +{tr['duration'] / US:.2f}s  {label}")
    return "\n".join(lines)


@mcp.tool()
def backup_project(project: str) -> str:
    """Copy a project folder to the backups folder."""
    return f"Backup saved: {backup(project_dir(project))}"


@mcp.tool()
def add_text(project: str, text: str, start: float, duration: float = 3.0) -> str:
    """Add a text/caption at `start` seconds for `duration` seconds.
    The project must already contain at least one text (any style): it is copied
    as a template, so the new text gets the same font and style."""
    def mutate(d):
        existing = segments(d, "text")
        if not existing:
            raise ValueError("Add any text in CapCut first; it is used as the style template.")
        track, tmpl = existing[-1]
        m = copy.deepcopy(material(d, tmpl["material_id"]))
        m["id"] = uid()
        try:
            content = json.loads(m["content"])
            content["text"] = text
            for st in content.get("styles", []):
                st["range"] = [0, len(text)]
            m["content"] = json.dumps(content, ensure_ascii=False)
        except (KeyError, ValueError):
            m["content"] = text
        d["materials"]["texts"].append(m)
        seg = copy.deepcopy(tmpl)
        seg["id"] = uid()
        seg["material_id"] = m["id"]
        refs = []
        for ref in seg.get("extra_material_refs", []):  # give the copy its own helper materials
            for cat, items in d["materials"].items():
                hit = next((x for x in items if isinstance(x, dict) and x.get("id") == ref), None) if isinstance(items, list) else None
                if hit:
                    new = copy.deepcopy(hit)
                    new["id"] = uid()
                    items.append(new)
                    refs.append(new["id"])
                    break
        seg["extra_material_refs"] = refs
        rng = {"start": round(start * US), "duration": round(duration * US)}
        seg["target_timerange"] = rng
        seg["source_timerange"] = {"start": 0, "duration": rng["duration"]}
        overlaps = any(s["target_timerange"]["start"] < rng["start"] + rng["duration"]
                       and rng["start"] < s["target_timerange"]["start"] + s["target_timerange"]["duration"]
                       for s in track["segments"])
        if overlaps:  # CapCut needs overlapping texts on separate tracks
            track = {**{k: v for k, v in track.items() if k != "segments"}, "id": uid(), "segments": []}
            d["tracks"].append(track)
        track["segments"].append(seg)
        track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        return f"Added text {text!r} at {start:.2f}s for {duration:.2f}s."
    return edit(project, mutate)


@mcp.tool()
def trim_clip(project: str, track: int, index: int, new_duration: float) -> str:
    """Shorten (or lengthen, within the source media) a clip. Use read_timeline for track/index."""
    def mutate(d):
        seg = d["tracks"][track]["segments"][index]
        dur = round(new_duration * US)
        m = material(d, seg.get("material_id")) or {}
        src = seg.get("source_timerange") or {"start": 0}
        if m.get("duration") and src["start"] + dur > m["duration"]:
            raise ValueError(f"Source media is only {m['duration'] / US:.2f}s long.")
        seg["target_timerange"]["duration"] = dur
        seg["source_timerange"] = {"start": src["start"], "duration": dur}
        return f"Clip [{track}][{index}] is now {new_duration:.2f}s."
    return edit(project, mutate)


@mcp.tool()
def remove_segment(project: str, track: int, index: int) -> str:
    """Delete one clip/text from the timeline. Use read_timeline for track/index."""
    def mutate(d):
        seg = d["tracks"][track]["segments"].pop(index)
        return f"Removed [{track}][{index}] (was at {seg['target_timerange']['start'] / US:.2f}s)."
    return edit(project, mutate)


if __name__ == "__main__":
    mcp.run()
