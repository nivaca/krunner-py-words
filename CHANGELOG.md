# Changelog

All notable changes to krunner-py-words. The releases, with their zip
files and signed RPMs, are on
[GitHub](https://github.com/nivaca/krunner-py-words/releases); the code
is also on [Codeberg](https://codeberg.org/nivaca/krunner-py-words). The
RPM for Fedora is on Copr, in `nivaca/krunner-py-words`.

## 1.1.2 — 2026-11-22

- `packaging/build-rpm.sh` copies the newest RPM into `dist/` too, in
  place of the older ones there.
- The contact email is now nicolasvaughan@proton.me.
- **Every release signed**: besides the signature inside the RPM, each
  file published comes with its detached signature (`.asc`), with
  `SHA256SUMS` and its signature, and with the public key (now the copy in
  `packaging/`); the tag of the version is signed too.
  `tools/release.py` checks each signature with the published key before
  anything is published (`tools/sign_release.py`). The README says how to
  check a download.

## 1.1.1 — 2026-11-17

- It requires Python 3.14 or later: the runner and the settings dialog
  stop with a message on an older Python. The RPM spec and the README
  say so too.
- The RPM signing key is pinned in `packaging/build-rpm.sh`: it signs
  only with that key (ed25519, valid until 2029), and says how to import
  it when it is missing; `tools/release.py` checks for it first. Its
  public key is in `packaging/`, and the README gives its fingerprint.
- This release has no new RPM; the one on Copr is still 1.1. The zip
  `krunner-py-words-1.1.1.zip` has the whole program, to install with
  `python3 install.py [--py-words FOLDER]`.

## 1.1 — 2026-11-11

- First version: py-words, the Latin dictionary, in KRunner (KDE Plasma
  6). After the prefix, a Latin word or a whole line gives its entries
  as you type (`pw amicorum`), and `pw ~e WORD` looks up a word of the
  language of the meanings. Each match shows the dictionary form in
  bold, with the meaning and the forms below it.
- Enter opens the search in the window of py-words. The actions copy the
  results of the entry, open the search in the dictionary online, and
  open the settings.
- A settings window (`pw ?`, the application menu, or
  `python3 settings_dialog.py`) for the prefix, the language of the
  meanings, the language of the interface and the number of results,
  kept in `~/.config/krunner-py-words/settings.ini`. The prefix is `pw`
  by default (it was `la` during development).
- **An RPM package for Fedora**, on Copr (`sudo dnf copr enable
  nivaca/krunner-py-words && sudo dnf install krunner-py-words`, which
  brings py-words too) and, signed, on the releases. `tools/release.py`
  makes a release.
- `install.py` and `uninstall.py` install it from the zip, without the
  RPM.
