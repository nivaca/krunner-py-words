# Registro de cambios

Los cambios notables de krunner-py-words. Las versiones publicadas, con
sus archivos zip y sus RPM firmados, están en
[GitHub](https://github.com/nivaca/krunner-py-words/releases); el código
está también en [Codeberg](https://codeberg.org/nivaca/krunner-py-words).
El RPM para Fedora está en Copr, en `nivaca/krunner-py-words`.

## Sin publicar

- `tools/zenodo.py`: la descripción del depósito es ahora el README entero
  de la etiqueta, en HTML. El borrador recibe además el colaborador (el
  director del proyecto), los idiomas, el copyright, el repositorio en
  GitHub, el lenguaje de programación y el estado del desarrollo; estos
  últimos, por la API de registros de Zenodo, porque la de depósitos no los
  admite. El token puede guardarse en el llavero del escritorio
  (`secret-tool store --label="Zenodo token" service zenodo`) en vez de en
  `$ZENODO_TOKEN`; `tools/zenodo.py check-token` dice si hay uno.

- `tools/zenodo.py` prepara el depósito de una versión en Zenodo. `collect`
  deja en `dist/zenodo/` el árbol de la etiqueta como
  `krunner-py-words-VERSIÓN-source.tar.gz`, con su firma, un `SHA256SUMS`
  del depósito, firmado, y la clave pública, y comprueba cada firma con solo
  esa clave (`--packages` añade los archivos de la versión). `upload` lo
  sube a Zenodo como borrador, versión nueva del depósito si ya lo hay, y
  nunca lo publica. `tools/release.py` reúne ahora el depósito después de la
  etiqueta y lo sube como borrador, salvo con `--no-zenodo`. Los metadatos
  están en `.zenodo.json`.
- `tools/zenodo.py`: la descripción del depósito deja fuera la línea que
  lleva a los README en otras lenguas y la sección Screenshots, cuyas
  imágenes Zenodo no muestra.

## 1.1.2 — 2026-11-22

- `packaging/build-rpm.sh` copia también el RPM más reciente en `dist/`,
  en lugar de los más viejos que haya allí.
- El correo de contacto es ahora nicolasvaughan@proton.me.
- **Cada versión firmada**: además de la firma dentro del RPM, cada
  archivo publicado trae su firma aparte (`.asc`), con `SHA256SUMS` y su
  firma, y con la clave pública (ahora la copia de `packaging/`); el tag
  de la versión va firmado también. `tools/release.py` comprueba cada
  firma con la clave publicada antes de publicar nada
  (`tools/sign_release.py`). El README explica cómo comprobar una
  descarga.

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
