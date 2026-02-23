import struct
import hashlib
import random
import math

# ==========================================================
# UTILIDADES BMP
# ==========================================================

def leer_bmp(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    offset = struct.unpack_from('<I', data, 10)[0]
    width  = struct.unpack_from('<i', data, 18)[0]
    height = struct.unpack_from('<i', data, 22)[0]
    row_size = (width * 3 + 3) & ~3

    header = bytearray(data[:offset])
    pixels = bytearray(data[offset:])

    return header, pixels, width, height, row_size


def guardar_bmp(filepath, header, pixels):
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(pixels)


# ==========================================================
# DERIVACIÓN DE CLAVE Y CIFRADO XOR
# ==========================================================

def derivar_clave(password: str, longitud: int) -> bytes:
    clave = b''
    contador = 0

    while len(clave) < longitud:
        bloque = hashlib.sha256(
            password.encode() + struct.pack('>I', contador)
        ).digest()
        clave += bloque
        contador += 1

    return clave[:longitud]


def cifrar_xor(mensaje: bytes, password: str) -> bytes:
    clave = derivar_clave(password, len(mensaje))
    return bytes(m ^ k for m, k in zip(mensaje, clave))


def descifrar_xor(cifrado: bytes, password: str) -> bytes:
    return cifrar_xor(cifrado, password)  # XOR es simétrico


# ==========================================================
# PERMUTACIÓN PSEUDOALEATORIA ÚNICA
# ==========================================================

def semilla_de_password(password: str) -> int:
    hash_bytes = hashlib.sha256(password.encode()).digest()
    return int.from_bytes(hash_bytes[:8], 'big')


def generar_permutacion(total_bytes: int, seed: int) -> list:
    rng = random.Random(seed)
    posiciones = list(range(total_bytes))
    rng.shuffle(posiciones)
    return posiciones


# ==========================================================
# EMBEDDING SEGURO
# ==========================================================

def embed_secure(src_path, dst_path, mensaje, password):
    header, pixels, _, _, _ = leer_bmp(src_path)

    msg_bytes = mensaje.encode('utf-8')
    msg_cifrado = cifrar_xor(msg_bytes, password)

    # BIG-ENDIAN para la longitud (consistente con la lectura)
    datos = struct.pack('>I', len(msg_bytes)) + msg_cifrado

    bits = [(byte >> i) & 1 for byte in datos for i in range(7, -1, -1)]
    total_bits = len(bits)

    if total_bits > len(pixels):
        raise ValueError("Mensaje demasiado grande para la imagen")

    seed = semilla_de_password(password)
    perm = generar_permutacion(len(pixels), seed)

    pixels_mod = bytearray(pixels)

    for pos, bit in zip(perm[:total_bits], bits):
        pixels_mod[pos] = (pixels_mod[pos] & 0xFE) | bit

    guardar_bmp(dst_path, header, pixels_mod)
    print(f"[OK] {len(msg_bytes)} bytes cifrados e incrustados en {dst_path}")


# ==========================================================
# EXTRACCIÓN SEGURA
# ==========================================================

def extract_secure(stego_path, password):
    _, pixels, _, _, _ = leer_bmp(stego_path)

    seed = semilla_de_password(password)
    perm = generar_permutacion(len(pixels), seed)

    # Leer longitud (32 bits, BIG-ENDIAN)
    msg_len = 0
    for pos in perm[:32]:
        msg_len = (msg_len << 1) | (pixels[pos] & 1)

    total_bits = 32 + msg_len * 8

    if total_bits > len(pixels):
        raise ValueError("Clave incorrecta o mensaje corrupto")

    msg_bits = [pixels[p] & 1 for p in perm[32:total_bits]]

    cifrado = bytearray()
    for i in range(0, len(msg_bits), 8):
        byte = 0
        for bit in msg_bits[i:i + 8]:
            byte = (byte << 1) | bit
        cifrado.append(byte)

    mensaje = descifrar_xor(bytes(cifrado), password)
    return mensaje.decode('utf-8')


# ==========================================================
# CHI-CUADRADO
# ==========================================================

def chi_cuadrado_lsb(filepath):
    _, pixels, _, _, _ = leer_bmp(filepath)

    ceros = sum(1 for b in pixels if (b & 1) == 0)
    unos  = len(pixels) - ceros
    esperado = len(pixels) / 2

    chi2 = ((ceros - esperado)**2 + (unos - esperado)**2) / esperado

    print(f"LSBs=0: {ceros}")
    print(f"LSBs=1: {unos}")
    print(f"χ² = {chi2:.4f}")
    print("→ χ² cercano a 0 indica distribución uniforme")

    return chi2


# ==========================================================
# PSNR
# ==========================================================

def calcular_psnr(original_path, stego_path):
    _, pix_orig, w, h, _ = leer_bmp(original_path)
    _, pix_steg, _, _, _ = leer_bmp(stego_path)

    mse = sum((a - b)**2 for a, b in zip(pix_orig, pix_steg)) / (w * h * 3)

    if mse == 0:
        return float('inf')

    psnr = 10 * math.log10(255**2 / mse)
    print(f"PSNR: {psnr:.2f} dB")
    return psnr


# ==========================================================
# PRUEBA PRINCIPAL
# ==========================================================

if __name__ == "__main__":

    CLAVE = "Telemática@2025"
    MENSAJE = "Datos confidenciales de la red 10.0.1.0/24"

    print("=== EMBEDDING ===")
    embed_secure("imagen.bmp", "stego_seguro.bmp", MENSAJE, CLAVE)

    print("\n=== EXTRACCIÓN CORRECTA ===")
    resultado = extract_secure("stego_seguro.bmp", CLAVE)
    print("Mensaje recuperado:", resultado)

    print("\n=== EXTRACCIÓN INCORRECTA ===")
    try:
        basura = extract_secure("stego_seguro.bmp", "claveWrong")
        print("Resultado:", basura[:30])
    except Exception as e:
        print("Error esperado:", e)

    print("\n=== PSNR ===")
    calcular_psnr("imagen.bmp", "stego_seguro.bmp")

    print("\n=== CHI-CUADRADO ===")
    print("Imagen original:")
    chi_cuadrado_lsb("imagen.bmp")
    print("Imagen esteganografiada:")
    chi_cuadrado_lsb("stego_seguro.bmp")