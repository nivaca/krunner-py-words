# Registro de cambios

Los cambios notables de krunner-py-words. Las versiones publicadas, con
sus archivos zip y sus RPM firmados, están en
[GitHub](https://github.com/nivaca/krunner-py-words/releases); el código
está también en [Codeberg](https://codeberg.org/nivaca/krunner-py-words).
El RPM para Fedora está en Copr, en `nivaca/krunner-py-words`.

## Sin publicar

- `packaging/build-rpm.sh` copia también el RPM más reciente en `dist/`,
  en lugar de los más viejos que haya allí.
- El correo de contacto es ahora nicolasvaughan@proton.me.

## 1.1.1 — 2026-11-17

- Requiere Python 3.14 o posterior: con un Python más viejo, el runner y
  el diálogo de configuración se detienen con un mensaje. La spec del RPM
  y el README también lo dicen.
- La clave con que se firma el RPM queda fijada en
  `packaging/build-rpm.sh`: el script firma solo con esa clave (ed25519,
  válida hasta 2029) y, si falta, explica cómo importarla;
  `tools/release.py` la busca antes que nada. Su clave pública está en
  `packaging/`, y el README da su huella.
- Esta versión no trae un RPM nuevo; el de Copr sigue siendo el 1.1. El
  zip `krunner-py-words-1.1.1.zip` contiene el programa completo, que se
  instala con `python3 install.py [--py-words FOLDER]`.

## 1.1 — 2026-11-11

- Primera versión: py-words, el diccionario latino, en KRunner (KDE
  Plasma 6). Tras el prefijo, una palabra latina o una línea entera da
  sus entradas a medida que se escribe (`pw amicorum`), y `pw ~e WORD`
  busca una palabra de la lengua de los significados. Cada resultado
  muestra la forma de diccionario en negrita y, debajo, el significado y
  las formas.
- Enter abre la búsqueda en la ventana de py-words. Las acciones copian
  los resultados de la entrada, abren la búsqueda en el diccionario en
  línea y abren la configuración.
- Una ventana de configuración (`pw ?`, el menú de aplicaciones o
  `python3 settings_dialog.py`) para el prefijo, la lengua de los
  significados, la lengua de la interfaz y el número de resultados, que
  se guardan en `~/.config/krunner-py-words/settings.ini`. El prefijo es
  `pw` por defecto (durante el desarrollo fue `la`).
- **Un paquete RPM para Fedora**, en Copr (`sudo dnf copr enable
  nivaca/krunner-py-words && sudo dnf install krunner-py-words`, que
  instala también py-words) y, firmado, entre las versiones publicadas.
  `tools/release.py` prepara una versión.
- `install.py` y `uninstall.py` lo instalan desde el zip, sin el RPM.
