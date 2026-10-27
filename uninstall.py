#!/usr/bin/env python3
"""Removes the py-words runner for the current user: the two files that
install.py wrote, and the runner that is running; then KRunner restarts.

    python3 uninstall.py

(The same as python3 install.py --uninstall.  This folder and py-words
are left as they are.)
"""

import install

if __name__ == '__main__':
    install.main(['--uninstall'])
