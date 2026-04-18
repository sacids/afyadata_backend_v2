import json
import base64
from django.conf import settings
from .models import * 






def xor_cipher(data, key):
    # Standard XOR logic: cycle the key to match data length
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def generate_qr_string(joining_url, qr_id, expires_on_iso, user=None):
    
    print('in generate qr string')
    """
    joining_url: The full link
    qr_id: The UUID/ID from your ProjectQRCode model
    expires_on_iso: String format of date (e.g. 2026-04-20T12:00:00Z)
    """
    # 1. Create JSON Payload
    payload_dict = {
        "id": str(qr_id),
        "url": joining_url,
        "exp": expires_on_iso
    }
    payload_json = json.dumps(payload_dict, separators=(',', ':')) # Compact JSON
    
    # 2. Select Key and Prefix
    if user:
        key = user.username
        prefix = "L"
    else:
        key = settings.AFYADATA_GLOBAL_KEY
        prefix = "G"

    # 3. Encrypt (XOR + Base64)
    ciphered = xor_cipher(payload_json, key)
    encoded = base64.b64encode(ciphered.encode()).decode()
    
    print(f"{prefix}:{encoded}")
    
    return f"{prefix}:{encoded}"


# utils.py - Add these functions alongside your existing generate_qr_string

def decode_qr_string(qr_string):
    """
    Decrypt and parse a QR code string.
    Returns the payload dict or None if invalid.
    """
    try:
        # Split prefix and encoded data
        if ':' not in qr_string:
            return None
        
        prefix, encoded = qr_string.split(':', 1)
        
        # Determine key based on prefix
        if prefix == 'L':
            # User-specific key - would need to know which user
            # This is typically handled by the view that knows the context
            return None
        elif prefix == 'G':
            key = settings.AFYADATA_GLOBAL_KEY
        else:
            return None
        
        # Decode base64
        ciphered = base64.b64decode(encoded).decode()
        
        # Decrypt XOR
        decrypted = xor_cipher(ciphered, key)
        
        # Parse JSON
        payload = json.loads(decrypted)
        
        return payload
    except Exception as e:
        print(f"Failed to decode QR string: {e}")
        return None


def generate_qr_image_data(qr_string, size=300):
    """
    Generate QR code image data as base64 for embedding in HTML.
    Requires qrcode library: pip install qrcode Pillow
    """
    import qrcode
    from io import BytesIO
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize if needed
    if size:
        img = img.resize((size, size))
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"








