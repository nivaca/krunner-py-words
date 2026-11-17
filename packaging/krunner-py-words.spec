# krunner-py-words: py-words, the Latin dictionary, in KRunner.
# Copyright (C) 2026 Nicolas Vaughan <nivaca@fastmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. This program is distributed WITHOUT ANY
# WARRANTY; see the LICENCE.txt file, or <https://www.gnu.org/licenses/>.
#
# Build with packaging/build-rpm.sh, which makes the source tarball. The
# version of the program is this spec's Version (tools/release.py reads it).

%global py_words_dir %{_datadir}/py-words

Name:           krunner-py-words
Version:        1.1.1
Release:        1%{?dist}
Summary:        py-words, the Latin dictionary, in KRunner

License:        GPL-3.0-or-later
URL:            https://github.com/nivaca/krunner-py-words
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  desktop-file-utils
# For %check, which looks a word up with the py-words package (from the
# Copr project nivaca/py-words).
BuildRequires:  py-words
BuildRequires:  python3-dbus
BuildRequires:  python3-gobject-base

Requires:       python3 >= 3.14
Requires:       py-words
Requires:       python3-dbus
Requires:       python3-gobject-base
# The settings window is Tk.
Requires:       python3-tkinter

%description
A runner for KRunner (KDE Plasma 6) that looks Latin words up in py-words
as you type: "pw amicorum" gives each entry, with its meaning and forms,
and "pw ~e friend" goes the other way. Enter opens the search in the
window of py-words; the actions copy the results, open the search online,
and open the settings of the runner.

%prep
%autosetup -n %{name}-%{version}

%build
# Nothing to build: the program is Python.

%install
# The runner's modules (not install.py and uninstall.py, which write the
# same files as this package, for the user, from a checkout).
install -d %{buildroot}%{_datadir}/%{name}
for f in dictionary.py krunner_py_words.py runner_settings.py \
         settings_dialog.py; do
    install -pm 0644 "$f" %{buildroot}%{_datadir}/%{name}/
done
%py_byte_compile %{python3} %{buildroot}%{_datadir}/%{name}

subst() {
    sed -e 's|@VERSION@|%{version}|' -e 's|@PYTHON@|%{python3}|' \
        -e 's|@DATADIR@|%{_datadir}/%{name}|' \
        -e 's|@PY_WORDS@|%{py_words_dir}|' "$1"
}
install -d %{buildroot}%{_datadir}/krunner/dbusplugins \
    %{buildroot}%{_datadir}/dbus-1/services
subst packaging/py-words.desktop.in \
    > %{buildroot}%{_datadir}/krunner/dbusplugins/py-words.desktop
subst packaging/io.github.nivaca.PyWordsKRunner.service.in \
    > %{buildroot}%{_datadir}/dbus-1/services/io.github.nivaca.PyWordsKRunner.service
subst packaging/krunner-py-words-settings.desktop.in \
    > krunner-py-words-settings.desktop
desktop-file-install --dir=%{buildroot}%{_datadir}/applications \
    krunner-py-words-settings.desktop

%check
desktop-file-validate \
    %{buildroot}%{_datadir}/applications/krunner-py-words-settings.desktop
! grep -rl '@[A-Z_]*@' %{buildroot}%{_datadir}/krunner \
    %{buildroot}%{_datadir}/dbus-1 %{buildroot}%{_datadir}/applications
# The installed runner loads (with D-Bus), and finds a word with the
# installed py-words, with no settings or cache of the builder's.
export HOME="$PWD/check-home" XDG_CONFIG_HOME= XDG_CACHE_HOME= \
    PY_WORDS_CACHE= PY_WORDS_CONFIG="$PWD/check-home/config"
cd %{buildroot}%{_datadir}/%{name}
%{python3} -c '
import dictionary, krunner_py_words
dictionary.use("%{py_words_dir}")
found = dictionary.Dictionary().matches("amicorum")
assert found[0].text.startswith("amicus"), found[0]
'
cd -

%files
%license LICENCE.txt
%doc README.md
%{_datadir}/%{name}/
%{_datadir}/krunner/dbusplugins/py-words.desktop
%{_datadir}/dbus-1/services/io.github.nivaca.PyWordsKRunner.service
%{_datadir}/applications/krunner-py-words-settings.desktop

%changelog
* Tue Nov 17 2026 Nicolas Vaughan <nivaca@fastmail.com> - 1.1.1-1
- Requires Python 3.14 or later

* Wed Nov 11 2026 Nicolas Vaughan <nivaca@fastmail.com> - 1.1-1
- First package: the runner, started by D-Bus, for every user, with the
  py-words package; its settings in the application menu
