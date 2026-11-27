#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of krunner-py-words. See the LICENCE.txt file for details.
"""Corre a la vez las pruebas de krunner-py-words:
python3 tools/test.py [-j N] [-v] [NOMBRE ...]

Cada archivo de pruebas (tests/test_*.py) corre con unittest en un proceso
propio, tantos a la vez como procesadores tenga el computador (-j lo
cambia), primero los más lentos; así, la suite entera tarda más o menos lo
que su archivo más lento, y no la suma de todos. Cada proceso tiene su
carpeta personal y su carpeta temporal.

Los NOMBRE eligen qué correr: un archivo (test_runner) o un patrón
(test_*sign*). Al final aparecen los archivos que fallaron, con su salida,
y los totales; -v muestra además cada archivo a medida que termina. El
código de salida es 1 si falló alguna prueba. (python3 -m unittest discover
-s tests las corre una tras otra, como antes.) Así las corre también
tools/release.py, antes de hacer nada.
"""

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
#  Los archivos que más tardan, que arrancan primero (los demás siguen en
#  orden alfabético): medidos con -v (2026-11-26: el primero es lo que tarda
#  la suite entera)
SLOW = ("test_zenodo.py", "test_runner.py")


def files(names: list[str]) -> list[Path]:
    """The test files to run, the slowest first."""
    found = sorted(TESTS.glob("test_*.py"))
    if names:
        found = [p for p in found if any(fnmatch.fnmatch(p.name, n)
                                         or fnmatch.fnmatch(p.stem, n)
                                         for n in names)]

    def rank(p: Path) -> int:
        return SLOW.index(p.name) if p.name in SLOW else len(SLOW)

    return sorted(found, key=rank)


def run(path: Path, work: Path, env: dict) -> tuple[Path, int, str, float]:
    """PATH run by unittest in a process of its own: (path, exit status,
    output, seconds)."""
    own = work / path.stem
    for sub in ("home", "tmp"):
        (own / sub).mkdir(parents=True, exist_ok=True)
    env = {**env, "HOME": str(own / "home"), "TMPDIR": str(own / "tmp")}
    start = time.time()
    #  Como "unittest discover -s tests", pero con solo este archivo
    done = subprocess.run([sys.executable, "-m", "unittest", "discover",
                           "-s", str(TESTS), "-p", path.name],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors="replace")
    return path, done.returncode, done.stdout, time.time() - start


def counts(output: str) -> dict[str, int]:
    """{'ran': n, 'failures': n, 'errors': n, 'skipped': n} of unittest's
    summary ("Ran 12 tests in 1.2s", then "OK (skipped=1)" or
    "FAILED (failures=1, errors=2)")."""
    found = {}
    if m := re.search(r"^Ran (\d+) tests?", output, re.MULTILINE):
        found["ran"] = int(m.group(1))
    if m := re.search(r"^(?:OK|FAILED) \(([^)]*)\)\s*$", output, re.MULTILINE):
        for key, n in re.findall(r"(\w+)=(\d+)", m.group(1)):
            found[key] = int(n)
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="tools/test.py",
        description="Run the tests of krunner-py-words, each file in a "
                    "process of its own, at once.")
    parser.add_argument("names", nargs="*", metavar="NAME",
                        help="files or patterns to run (default: all)")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 2,
                        help="how many at a time (default: the processors)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show each file as it ends")
    args = parser.parse_args(argv)
    todo = files(args.names)
    if not todo:
        print("tools/test.py: no tests match " + " ".join(args.names),
              file=sys.stderr)
        return 2
    work = Path(tempfile.mkdtemp(prefix="krunner-py-words-tests-"))
    env = {**os.environ}
    start = time.time()
    failed: list[tuple[Path, str]] = []
    totals: dict[str, int] = {}
    try:
        with ThreadPoolExecutor(max(1, args.jobs)) as pool:
            jobs = [pool.submit(run, path, work, env) for path in todo]
            for n, job in enumerate(as_completed(jobs), 1):
                path, status, output, seconds = job.result()
                found = counts(output)
                for k, v in found.items():
                    totals[k] = totals.get(k, 0) + v
                # (5: unittest no encontró pruebas en el archivo; no es un fallo)
                if status not in (0, 5):
                    failed.append((path, output))
                if args.verbose or status not in (0, 5):
                    mark = "ok" if status in (0, 5) else "FAILED"
                    print(f"[{n}/{len(todo)}] {path.name}: "
                          f"{found.get('ran', 0)} ran, {seconds:.1f}s, {mark}",
                          flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    for path, output in failed:
        print(f"\n{'=' * 70}\n{path.name}\n{'=' * 70}\n{output.rstrip()}")
    said = ", ".join(f"{v} {k}" for k, v in sorted(totals.items()))
    print(f"\n{said} ({len(todo)} files) in {time.time() - start:.1f}s: "
          + (f"FAILED ({len(failed)} files)" if failed else "OK"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
