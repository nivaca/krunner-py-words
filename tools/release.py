#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of krunner-py-words. See the LICENCE.txt file for details.
"""Publishes a release of krunner-py-words on GitHub (with gh) and on
Codeberg (with tea): the tag vVERSION (the Version of the spec,
packaging/krunner-py-words.spec), signed, with the signed RPM attached,
with its detached signature (FILE.asc), SHA256SUMS and its signature, and
the public key that checks them all; and builds it on Copr.

Everything is signed with the project's key (SIGNING_KEY of
packaging/build-rpm.sh), and every signature is checked, against the public
key published, before anything is published.

    python3 tools/release.py [--redo] [--notes TEXT | --notes-file FILE]
                             [--no-build] [--no-copr]
                             [--only github|codeberg] [--dry-run] [--yes]

In order, each step only if it is needed:

1. checks that the repository is on main, with nothing left to commit,
   that gh, tea, gpg, rpmbuild and copr-cli are installed, and that the
   signing key is in gpg;
2. makes the signed RPM in build/rpm/ (packaging/build-rpm.sh --sign,
   which checks its signature; gpg asks for the passphrase), unless
   --no-build (then the one in build/rpm/ is used); then signs it
   (tools/sign_release.py: FILE.asc, dist/SHA256SUMS and its .asc), and
   checks each signature with only the public key that is published
   (packaging/RPM-GPG-KEY-krunner-py-words);
3. tags HEAD as vVERSION, a tag signed with the same key (git tag --sign),
   and checks it (git tag --verify).  If the tag is there already on
   another commit, it stops, unless --redo moves it;
4. pushes main and the tag to the remote (origin, whose push addresses are
   GitHub and Codeberg; --redo pushes the tag with --force).  Whether each
   forge has the tag already is asked of each push address, as the remote
   may have no address to fetch from;
5. on each forge, makes the release of the tag, or keeps the one there is,
   and attaches the files to it, replacing those of the same name;
6. sends the source RPM to Copr (copr-cli build, project
   nivaca/krunner-py-words), unless --no-copr.  Copr builds it for each Fedora of
   the project and signs it with its own key; each build needs a higher
   version-release than the last, so the spec must have been bumped
   (rpmdev-bumpspec, see packaging/COPR.org).

Before doing anything, it shows the commands it will run and asks; --yes
does not ask, --dry-run only shows them.  The notes of a new release are
--notes, --notes-file, or else made by GitHub from the commits (on
Codeberg, none); a release that is there keeps its notes.

The repositories are found from the push addresses of the remote; tea uses
the login named codeberg unless --tea-login says another.

The deposit for Zenodo is collected in dist/zenodo/ after the tag
(tools/zenodo.py collect: the tree of the tag, signed, with SHA256SUMS and
the public key), and at the end uploaded to Zenodo and published (the token in
$ZENODO_TOKEN or the keyring), unless --no-zenodo. It is published there, with a new DOI;
with --zenodo-draft it is left as a draft, to publish by hand.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

if sys.version_info < (3, 14):
    sys.exit("krunner-py-words needs Python 3.14 or later.")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NAME = "krunner-py-words"
BRANCH = "main"
#  Where tea runs: outside the repository, as tea reads the remote's fetch
#  address there (which origin may not have) even when --repo is given
TEA_CWD = tempfile.gettempdir()
FORGES = {"github": "github.com", "codeberg": "codeberg.org"}
SPEC = os.path.join("packaging", f"{NAME}.spec")
#  La clave pública que va con cada versión, y que comprueba todas sus firmas
PUBLIC_KEY = os.path.join("packaging", f"RPM-GPG-KEY-{NAME}")
SUMS = os.path.join("dist", "SHA256SUMS")
COPR_PROJECT = NAME             # (of the copr-cli user, nivaca)


def zenodo_token() -> bool:
    """Whether tools/zenodo.py finds a Zenodo token, in $ZENODO_TOKEN or
    in the desktop keyring (secret-tool)."""
    tool = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "zenodo.py")
    done = subprocess.run([sys.executable, tool, "check-token"],
                          capture_output=True, check=False)
    return done.returncode == 0


def spec_query(fmt: str) -> str:
    try:
        return subprocess.run(
            ["rpmspec", "-q", "--srpm", "--qf", fmt, SPEC],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("release.py: rpmspec cannot read the spec (sudo dnf install rpm-build)")


#  The version is the spec's: a new one is made with
#  rpmdev-bumpspec -n X.Y -c "..." packaging/krunner-py-words.spec
VERSION = spec_query("%{version}")
TAG = f"v{VERSION}"


def signing_key() -> str:
    """The project's signing key, as packaging/build-rpm.sh pins it."""
    with open(os.path.join(ROOT, "packaging", "build-rpm.sh"), encoding="utf-8") as f:
        m = re.search(r'SIGNING_KEY="\$\{SIGNING_KEY:-([0-9A-F]{40})\}"', f.read())
    return m.group(1) if m else ""


def rpm_nvr() -> str:
    """NAME-VERSION-RELEASE of the RPM that packaging/build-rpm.sh makes, as
    its spec says (krunner-py-words-1.1-1.fc45)."""
    return spec_query("%{name}-%{version}-%{release}")


def rpm() -> str:
    return os.path.join("build", "rpm", "RPMS", "noarch", rpm_nvr() + ".noarch.rpm")


def srpm() -> str:
    return os.path.join("build", "rpm", "SRPMS", rpm_nvr() + ".src.rpm")


class Release:
    """The steps, run (or only shown) in order."""

    def __init__(self, args):
        self.args = args
        self.planned = []           # (description, command, folder)

    # ---- running -------------------------------------------------------- #
    def read(self, *command, check=True, cwd=ROOT) -> str:
        """The output of COMMAND (which only reads, so it runs even with
        --dry-run)."""
        out = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        if check and out.returncode != 0:
            sys.exit(f"release.py: {shlex.join(command)}: "
                     f"{(out.stderr or out.stdout).strip()}")
        return out.stdout.strip() if out.returncode == 0 else ""

    def plan(self, description: str, *command, cwd=ROOT):
        self.planned.append((description, list(command), cwd))

    def run_plan(self):
        if not self.planned:
            print("Nothing to do.")
            return
        print(f"Releasing {TAG}:")
        for description, command, cwd in self.planned:
            where = "" if cwd == ROOT else f"(in {cwd}) "
            print(f"\n  # {description}\n  {where}{shlex.join(command)}")
        print()
        if self.args.dry_run:
            return
        if not self.args.yes:
            answer = input("Run these commands? [y/N] ").strip().lower()
            if answer not in ("y", "yes", "s", "sí", "si"):
                sys.exit("Nothing done.")
        for description, command, cwd in self.planned:
            print(f"\n==> {description}", flush=True)
            if subprocess.run(command, cwd=cwd).returncode != 0:
                sys.exit(f"release.py: failed: {shlex.join(command)}\n"
                         "The steps before it were done; after fixing the cause, "
                         "run the script again (with --redo if the tag was "
                         "already moved).")
        print(f"\nReleased {TAG}.")

    # ---- checks --------------------------------------------------------- #
    def check(self):
        tools = ("git", "gpg") + tuple(t for t, f in (("gh", "github"), ("tea", "codeberg"))
                                 if f in self.forges)
        tools += ("rpmbuild",) + (() if self.args.no_copr else ("copr-cli",))
        for tool in tools:
            if not shutil.which(tool):
                sys.exit(f"release.py: {tool} is not installed")
        #  Todo se firma, siempre: sin la clave no hay versión
        key = signing_key()
        if not key or subprocess.run(["gpg", "--batch", "--list-secret-keys", key],
                                     capture_output=True).returncode != 0:
            sys.exit(f"release.py: the signing key {key or '(none)'} is not in this "
                     "machine's gpg keyring; import it first (see packaging/COPR.org)")
        if not os.path.isfile(os.path.join(ROOT, PUBLIC_KEY)):
            sys.exit(f"release.py: there is no {PUBLIC_KEY}, the public key published "
                     "with the release")
        self.read("git", "rev-parse", "--git-dir")      # (stops if not a repository)
        branch = self.read("git", "rev-parse", "--abbrev-ref", "HEAD")
        if branch != BRANCH:
            sys.exit(f"release.py: on branch {branch}, not {BRANCH}")
        if self.read("git", "status", "--porcelain"):
            message = "there are changes not committed (see git status)"
            if not self.args.dry_run:
                sys.exit(f"release.py: {message}")
            print(f"release.py: (dry run) {message}", file=sys.stderr)

    def push_urls(self) -> list[str]:
        return self.read("git", "remote", "get-url", "--push", "--all",
                         self.args.remote).split("\n")

    def repos(self) -> dict:
        """{forge: (owner/name, push address)}, from the remote."""
        found = {}
        for url in self.push_urls():
            m = re.search(r"(github\.com|codeberg\.org)[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", url)
            if m:
                found["github" if "github" in m[1] else "codeberg"] = (m[2], url)
        for forge in self.forges:
            if forge not in found:
                sys.exit(f"release.py: the remote {self.args.remote} does not push "
                         f"to {FORGES[forge]} (git remote -v)")
        return found

    # ---- steps ---------------------------------------------------------- #
    def build(self):
        if self.args.no_build:
            for f in self.files:
                if not os.path.isfile(os.path.join(ROOT, f)):
                    sys.exit(f"release.py: there is no {f} (leave out --no-build "
                             "to make it)")
            return
        self.plan("Make the signed RPM", "packaging/build-rpm.sh", "--sign")

    def sign(self):
        """Every file published signed (FILE.asc), with SHA256SUMS and its
        signature, and each signature checked with only the public key
        published."""
        signed = [f for f in self.files if f != PUBLIC_KEY]
        self.plan("Sign the files, and check each signature with the published key",
                  sys.executable, os.path.join("tools", "sign_release.py"), "--key",
                  signing_key(), "--public", PUBLIC_KEY, "--sums", SUMS, *signed)
        self.files = signed + [f + ".asc" for f in signed] + [SUMS, SUMS + ".asc",
                                                              PUBLIC_KEY]

    def tag(self, repos: dict):
        head = self.read("git", "rev-parse", "HEAD")
        tagged = self.read("git", "rev-parse", "--verify", "--quiet",
                           f"refs/tags/{TAG}^{{commit}}", check=False)
        if tagged == head:
            pass
        elif tagged and not self.args.redo:
            sys.exit(f"release.py: {TAG} is already the tag of {tagged[:7]}, not of "
                     f"HEAD ({head[:7]}); --redo moves it (and replaces the files "
                     "of the releases)")
        else:
            self.plan("Move the tag to HEAD, signed" if tagged else "Tag HEAD, signed",
                      "git", "tag", "--force", "--sign", "--local-user", signing_key(),
                      TAG, "--message", TAG)
            self.plan("Check the signature of the tag", "git", "tag", "--verify", TAG)
        self.plan(f"Push {BRANCH}", "git", "push", self.args.remote, BRANCH)
        #  With --redo the tag is always pushed with --force (to all the
        #  push addresses of the remote)
        if self.args.redo:
            self.plan("Push the tag (replacing it on the forges)", "git", "push",
                      "--force", self.args.remote, f"refs/tags/{TAG}")
            return
        #  Asked of each forge (the remote may have no address to fetch from)
        on_forges = []
        for forge in self.forges:
            url = repos[forge][1]
            out = self.read("git", "ls-remote", "--tags", url, f"refs/tags/{TAG}^{{}}",
                            check=False)
            there = out.split()[0] if out else ""
            if there and there != head:
                sys.exit(f"release.py: on {FORGES[forge]}, {TAG} is the tag of "
                         f"{there[:7]}; --redo moves it")
            on_forges.append(there == head)
        if not all(on_forges):
            self.plan("Push the tag", "git", "push", self.args.remote, f"refs/tags/{TAG}")

    def notes(self, github: bool) -> list[str]:
        if self.args.notes_file:
            return ["--notes-file" if github else "--note-file", self.args.notes_file]
        if self.args.notes:
            return ["--notes" if github else "--note", self.args.notes]
        return ["--generate-notes"] if github else []

    def github(self, repo: str):
        exists = subprocess.run(["gh", "release", "view", TAG, "--repo", repo],
                                cwd=ROOT, capture_output=True).returncode == 0
        if exists:
            self.plan("GitHub: attach the files to the release (replacing those there)",
                      "gh", "release", "upload", TAG, *self.files, "--clobber",
                      "--repo", repo)
        else:
            self.plan("GitHub: make the release", "gh", "release", "create", TAG,
                      *self.files, "--title", TAG, "--verify-tag", *self.notes(True),
                      "--repo", repo)

    def codeberg(self, repo: str):
        where = ["--repo", repo, "--login", self.args.tea_login]
        files = [os.path.join(ROOT, f) for f in self.files]   # (tea runs elsewhere)
        releases = self.tea_json("releases", "ls", "--limit", "50", *where)
        exists = any(TAG in (r.get("tagname"), r.get("tag")) for r in releases)
        if exists:
            names = {a.get("name") for a in self.tea_json("releases", "assets", "ls",
                                                          TAG, *where)}
            old = [os.path.basename(f) for f in self.files if os.path.basename(f) in names]
            if old:
                self.plan("Codeberg: remove the files of the same name (tea cannot "
                          "replace them)", "tea", "releases", "assets", "delete", TAG,
                          *old, "--confirm", *where, cwd=TEA_CWD)
            self.plan("Codeberg: attach the files to the release", "tea", "releases",
                      "assets", "create", TAG, *files, *where, cwd=TEA_CWD)
        else:
            assets = [a for f in files for a in ("--asset", f)]
            self.plan("Codeberg: make the release", "tea", "releases", "create",
                      "--tag", TAG, "--title", TAG, *self.notes(False), *assets, *where,
                      cwd=TEA_CWD)

    def copr(self):
        if self.args.no_build and not os.path.isfile(os.path.join(ROOT, srpm())):
            sys.exit(f"release.py: there is no {srpm()} (leave out --no-build to make it)")
        self.plan(f"Copr: build the RPM (project {COPR_PROJECT})", "copr-cli", "build",
                  COPR_PROJECT, srpm())

    def tea_json(self, *command) -> list[dict]:
        """The rows tea gives in JSON, with its keys made plain ("tag-_name" is
        tagname)."""
        result = subprocess.run(["tea", *command, "--output", "json"], cwd=TEA_CWD,
                                capture_output=True, text=True)
        if result.returncode != 0:
            error = (result.stderr or result.stdout).strip()
            if "couldn't be found" in error or "404" in error:
                repo = command[command.index("--repo") + 1]
                sys.exit(f"release.py: Codeberg has no repository {repo}, or the tea "
                         f"login {self.args.tea_login!r} cannot see it (make it on "
                         "codeberg.org first, or use --only github)")
            sys.exit(f"release.py: tea {shlex.join(command)}: {error}")
        out = result.stdout.strip()
        try:
            rows = json.loads(out or "[]")
        except ValueError:
            sys.exit(f"release.py: tea {' '.join(command)}: not JSON: {out[:200]}")
        return [{re.sub("[^a-z]", "", k.lower()): v for k, v in r.items()} for r in rows]

    # ---- all ------------------------------------------------------------ #
    def zenodo_collect(self):
        """The deposit of the release for Zenodo, in dist/zenodo/ (tools/zenodo.py): the tree of the tag, signed,
        with SHA256SUMS and the public key, each signature checked with only that key."""
        self.plan("Zenodo: collect the deposit in dist/zenodo/", sys.executable, "tools/zenodo.py", "collect",
                  "--tag", TAG)

    def zenodo_upload(self):
        """Unless --no-zenodo, dist/zenodo/ uploaded to Zenodo and published (with
        --zenodo-draft, only as a draft, published there by hand)."""
        if self.args.no_zenodo:
            return
        # (sin token se para aquí, antes de hacer nada, y no al final de la versión)
        if not zenodo_token() and not self.args.dry_run:
            sys.exit("release.py: the upload to Zenodo needs a token (see tools/zenodo.py check-token); "
                     "--no-zenodo leaves it out")
        publish = [] if self.args.zenodo_draft else ["--publish"]
        what = " as a draft (not published)" if self.args.zenodo_draft else " and publish it"
        self.plan("Zenodo: upload the deposit" + what, sys.executable, "tools/zenodo.py", "upload", *publish)

    def __call__(self):
        args = self.args
        self.forges = [args.only] if args.only else ["github", "codeberg"]
        self.files = [rpm(), PUBLIC_KEY]
        self.check()
        repos = self.repos()
        self.build()
        self.sign()
        self.tag(repos)
        self.zenodo_collect()
        for forge in self.forges:
            getattr(self, forge)(repos[forge][0])
        if not args.no_copr:
            self.copr()
        self.zenodo_upload()
        self.run_plan()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/release.py",
        description=f"Publish {TAG} on GitHub and Codeberg, with the signed RPM "
                    "and the signatures of the files, and build it on Copr.")
    parser.add_argument("--redo", action="store_true",
                        help=f"move {TAG} to HEAD if it is on another commit (here and "
                             "on the forges), and replace the files of the releases")
    notes = parser.add_mutually_exclusive_group()
    notes.add_argument("--notes", metavar="TEXT", help="the notes of a new release")
    notes.add_argument("--notes-file", metavar="FILE",
                       help="the notes of a new release, from FILE")
    parser.add_argument("--no-build", action="store_true",
                        help="use the RPM in build/rpm/, without making it again")
    parser.add_argument("--no-copr", action="store_true",
                        help="do not send it to Copr")
    parser.add_argument("--only", choices=("github", "codeberg"),
                        help="publish on one forge only")
    parser.add_argument("--remote", default="origin",
                        help="the remote to push to (default: origin)")
    parser.add_argument("--tea-login", default="codeberg",
                        help="the login of tea for Codeberg (default: codeberg)")
    parser.add_argument("--no-zenodo", action="store_true",
                        help="don't upload dist/zenodo/ to Zenodo (by default it is uploaded and "
                             "published, with the token in $ZENODO_TOKEN or the keyring)")
    parser.add_argument("--zenodo-draft", action="store_true",
                        help="upload it to Zenodo as a draft, not published")
    parser.add_argument("--zenodo", action="store_true",
                        help="(the upload to Zenodo is made always now, unless --no-zenodo: kept "
                             "for older scripts)")
    parser.add_argument("-n", "--dry-run", action="store_true", help="only show the commands")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="do not ask before running them")
    args = parser.parse_args(argv)
    if args.notes_file:
        args.notes_file = os.path.abspath(args.notes_file)
    Release(args)()


if __name__ == "__main__":
    main()
