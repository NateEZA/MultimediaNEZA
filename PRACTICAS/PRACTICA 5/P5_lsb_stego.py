import struct
import math

# --- PASO 1 y 2: Funciones Base y Empotrado ---
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

def embed_lsb(src_path, dst_path, mensaje):
    header, pixels, width, height, row_size = leer_bmp(src_path)
    msg_bytes = mensaje.encode('utf-8')
    msg_len = len(msg_bytes)
    # Empaquetar longitud (4 bytes) + mensaje
    data_to_hide = struct.pack('>I', msg_len) + msg_bytes
    
    bits = []
    for byte in data_to_hide:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    
    if len(bits) > len(pixels):
        raise ValueError('Mensaje demasiado largo')
    
    pixels_mod = bytearray(pixels)
    for idx, bit in enumerate(bits):
        pixels_mod[idx] = (pixels_mod[idx] & 0xFE) | bit
    
    guardar_bmp(dst_path, header, pixels_mod)
    print(f'[OK] Mensaje incrustado en {dst_path}')

# --- PASO 3: Función de Extracción ---
def extract_lsb(stego_path):
    _, pixels, _, _, _ = leer_bmp(stego_path)
    
    # Leer primeros 32 bits (4 bytes) para la longitud del mensaje
    len_bits = [pixels[i] & 1 for i in range(32)]
    msg_len = 0
    for b in len_bits:
        msg_len = (msg_len << 1) | b
    
    # Leer los siguientes msg_len * 8 bits
    total_bits = 32 + (msg_len * 8)
    msg_bits = [pixels[i] & 1 for i in range(32, total_bits)]
    
    # Reconstruir bytes
    msg_bytes = bytearray()
    for i in range(0, len(msg_bits), 8):
        byte = 0
        for bit in msg_bits[i:i+8]:
            byte = (byte << 1) | bit
        msg_bytes.append(byte)
    
    return msg_bytes.decode('utf-8')

# --- PASO 5: Cálculo de PSNR ---
def calcular_psnr(original_path, stego_path):
    _, pix_orig, w, h, rs = leer_bmp(original_path)
    _, pix_steg, _, _, _  = leer_bmp(stego_path)
    
    # El MSE se calcula sobre la diferencia de los bytes
    mse = sum((a - b)**2 for a, b in zip(pix_orig, pix_steg)) / (w * h * 3)
    
    if mse == 0:
        return float('inf')
    
    psnr = 10 * math.log10(255**2 / mse)
    print(f'MSE:  {mse:.6f}')
    print(f'PSNR: {psnr:.2f} dB (>40 dB: cambio imperceptible)')
    return psnr

# --- PASO 4: Prueba de ida y vuelta ---
if __name__ == "__main__":
    # Ajusta las rutas a tus archivos reales
    orig = './images/400x400.bmp'
    stego = './images/stego.bmp'
    mensaje_original = 'TELEMÁTICA SECRETA 2025'
    
    try:
        # Ocultar
        embed_lsb(orig, stego, mensaje_original)
        
        # Recuperar
        recuperado = extract_lsb(stego)
        print(f'Mensaje recuperado: {recuperado}')
        
        # Validar
        assert recuperado == mensaje_original, '¡Error en la extracción!'
        print('Prueba exitosa.')
        
        # Analizar calidad
        calcular_psnr(orig, stego)
        
    except FileNotFoundError:
        print("Asegúrate de que la carpeta './images/' y 'volcan.bmp' existan.")