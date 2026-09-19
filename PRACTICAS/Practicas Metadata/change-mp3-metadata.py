"""Cambia la portada de un único archivo MP3 local.

Instalación: pip install mutagen
Uso: python change-mp3-metadata.py "audio.mp3" "portada.jpg"
"""

from pathlib import Path
import sys

from mutagen.id3 import APIC, ID3, ID3NoHeaderError
from mutagen.mp3 import MP3


def cambiar_portada(ruta_audio: str, ruta_imagen: str) -> None:
	audio = Path(ruta_audio)
	imagen = Path(ruta_imagen)

	if not audio.is_file():
		raise FileNotFoundError(f"No existe el audio: {audio}")
	if not imagen.is_file():
		raise FileNotFoundError(f"No existe la imagen: {imagen}")

	mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(
		imagen.suffix.lower()
	)
	if mime is None:
		raise ValueError("La portada debe ser JPG o PNG.")

	MP3(audio)  # valida que el archivo sea un MP3
	try:
		etiquetas = ID3(audio)
	except ID3NoHeaderError:
		etiquetas = ID3()

	etiquetas.delall("APIC")
	etiquetas.add(APIC(
		encoding=3,
		mime=mime,
		type=3,
		desc="Cover",
		data=imagen.read_bytes(),
	))
	etiquetas.save(audio, v2_version=3)


def main() -> None:
	if len(sys.argv) == 3:
		ruta_audio, ruta_imagen = sys.argv[1], sys.argv[2]
	else:
		ruta_audio = input("Ruta del audio MP3: ").strip().strip('"')
		ruta_imagen = input("Ruta de la portada JPG/PNG: ").strip().strip('"')

	try:
		cambiar_portada(ruta_audio, ruta_imagen)
		print(f"Portada actualizada en: {ruta_audio}")
	except (OSError, ValueError) as error:
		print(f"Error: {error}", file=sys.stderr)
		raise SystemExit(1)


if __name__ == "__main__":
	main()
