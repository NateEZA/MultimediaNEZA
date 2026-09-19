from pathlib import Path
import argparse

from mutagen.mp3 import MP3


def obtener_metadata(ruta: str) -> dict:
	"""Obtiene la metadata de un archivo MP3 local."""
	archivo = Path(ruta).expanduser()
	if not archivo.is_file():
		raise FileNotFoundError(f"No existe el archivo: {archivo}")
	if archivo.suffix.lower() != ".mp3":
		raise ValueError("El archivo debe tener extensión .mp3")

	audio = MP3(archivo)
	metadata = {
		"archivo": str(archivo.resolve()),
		"nombre": archivo.name,
		"tamaño_bytes": archivo.stat().st_size,
		"duración_segundos": round(audio.info.length, 2),
		"bitrate_kbps": round(audio.info.bitrate / 1000) if audio.info.bitrate else None,
		"frecuencia_hz": audio.info.sample_rate,
		"canales": audio.info.channels,
	}

	# Los campos ID3 pueden contener listas; se convierten a texto legible.
	for clave, valores in audio.tags.items() if audio.tags else []:
		if clave.startswith("T") or clave in {"COMM", "USLT"}:
			metadata[clave] = "; ".join(map(str, valores))

	return metadata


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Muestra la metadata de un archivo MP3 local.")
	parser.add_argument("archivo", nargs="?", help="Ruta del archivo MP3")
	args = parser.parse_args()
	ruta = args.archivo or input("Ruta del archivo MP3: ").strip().strip('"')

	try:
		for campo, valor in obtener_metadata(ruta).items():
			print(f"{campo}: {valor}")
	except (FileNotFoundError, ValueError, OSError) as error:
		print(f"Error: {error}")
