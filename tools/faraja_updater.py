"""FarajaWebServer external updater/rollback helper.

Run this helper AFTER the GUI exits; it never replaces a running executable.

Usage:
    python tools/faraja_updater.py --app-root <dir> --apply <release.zip>
    python tools/faraja_updater.py --app-root <dir> --rollback <backup-dir>

Adapted from the V15 PRO production-hardening package for the V16 layout
(application source is MiniServer.py, staged metadata in updates/staged.json).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

MAX_ARCHIVE = 500 * 1024 * 1024
MAX_FILES = 10000
MAX_UNPACKED = 2 * 1024 * 1024 * 1024

SOURCE_NAMES = ("MiniServer.py",)
PRESERVE_TREE = ("MiniServer.py", "assets", "tools", "components.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def safe_members(z: zipfile.ZipFile):
    total = 0
    names = []
    for i, info in enumerate(z.infolist()):
        if i >= MAX_FILES:
            raise RuntimeError("archive contains too many files")
        name = info.filename.replace("\\", "/")
        p = Path(name)
        if p.is_absolute() or ".." in p.parts:
            raise RuntimeError(f"unsafe archive path: {name}")
        total += max(0, info.file_size)
        if total > MAX_UNPACKED:
            raise RuntimeError("archive unpacked size exceeds safety limit")
        names.append((info, name))
    return names


def atomic_replace(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name("." + dst.name + ".new")
    shutil.copy2(src, tmp)
    with tmp.open("r+b") as f:
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, dst)


def _find_source(root: Path):
    for name in SOURCE_NAMES:
        for cand in root.rglob(name):
            return cand
    return None


def apply_source(app_root: Path, archive: Path):
    if archive.stat().st_size > MAX_ARCHIVE:
        raise RuntimeError("archive exceeds 500 MB")
    if not zipfile.is_zipfile(archive):
        raise RuntimeError("invalid ZIP")
    staging = app_root / "updates" / ("staging-" + str(int(time.time())))
    staging.mkdir(parents=True, exist_ok=False)
    backup = app_root / "updates" / ("rollback-" + time.strftime("%Y%m%d-%H%M%S"))
    try:
        with zipfile.ZipFile(archive) as z:
            members = safe_members(z)
            if z.testzip():
                raise RuntimeError("ZIP CRC verification failed")
            py = [n for _, n in members
                  if Path(n).name.lower().startswith("miniserver") and n.lower().endswith(".py")]
            if not py:
                raise RuntimeError("application source missing")
            z.extractall(staging)
        source = _find_source(staging)
        if source is None:
            raise RuntimeError("MiniServer.py missing from staged package")
        # Preserve the current install; only replace source/assets present in the package.
        backup.mkdir(parents=True, exist_ok=False)
        for rel in PRESERVE_TREE:
            old = app_root / rel
            if old.exists():
                target = backup / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(old, target) if old.is_dir() else shutil.copy2(old, target)
        new_root = source.parent
        for rel in ("MiniServer.py", "assets"):
            candidate = new_root / rel
            if candidate.exists():
                target = app_root / rel
                if candidate.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(candidate, target)
                else:
                    atomic_replace(candidate, target)
        marker = app_root / "updates" / "last_apply.json"
        marker.write_text(json.dumps({
            "applied_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "archive_sha256": sha256(archive),
            "rollback": str(backup.relative_to(app_root)),
        }, indent=2), encoding="utf-8")
        print(f"ROLLBACK={backup}")
        return backup
    except Exception:
        shutil.rmtree(backup, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def rollback(app_root: Path, backup: Path):
    backup = backup.resolve()
    if not backup.is_dir() or app_root.resolve() not in backup.parents:
        raise RuntimeError("rollback directory must be inside app_root")
    src = backup / "MiniServer.py"
    if not src.is_file():
        raise RuntimeError("rollback source missing")
    atomic_replace(src, app_root / "MiniServer.py")
    print("ROLLBACK_OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description="FarajaWebServer external updater")
    ap.add_argument("--app-root", required=True)
    ap.add_argument("--apply")
    ap.add_argument("--rollback")
    args = ap.parse_args(argv)
    root = Path(args.app_root).resolve()
    if args.apply and args.rollback:
        ap.error("choose --apply or --rollback")
    if args.apply:
        apply_source(root, Path(args.apply).resolve())
    elif args.rollback:
        rollback(root, Path(args.rollback))
    else:
        ap.error("one action required")


if __name__ == "__main__":
    main()
