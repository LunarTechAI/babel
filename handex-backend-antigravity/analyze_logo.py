import fitz
import base64
import json
import sys
import zlib

def analyze_image(image_path):
    try:
        # Open image with pymupdf
        # Use Pixmap to get raw samples
        pix = fitz.Pixmap(image_path)
        
        # Ensure it's RGB (drop alpha if needed, or handle it)
        # PDF inline images with alpha are tricky (require SMask). 
        # For simplicity, let's assume we blend with white or just drop alpha if it's a simple logo.
        # Or better, if it has alpha, we might need a Soft Mask.
        # Let's check if it has alpha.
        if pix.alpha:
            print("Image has alpha channel.")
            # Convert to RGB, blending with white background for the 'white' logo (which is black text usually?)
            # Wait, 'white logo' means white text on black background. 'Black logo' means black text on white background.
            # If the uploaded logo is black text with transparent background:
            # - On white background: use as is (or blend with white).
            # - On black background: invert colors.
            
            # Let's just get the alpha mask and RGB separately if possible, or just flatten.
            # For inline images, handling alpha is complex (need /SMask entry which refers to another XObject or dictionary).
            # Simplest is to ignore alpha if it's just a simple shape, or flatten it.
            pass

        # Let's try to just get RGB samples.
        if pix.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
            
        width = pix.w
        height = pix.h
        print(f"Width: {width}")
        print(f"Height: {height}")
        
        # Normal samples
        samples = pix.samples
        compressed = zlib.compress(samples)
        b64_normal = base64.b64encode(compressed).decode('utf-8')
        
        print(f"Normal Base64 (len={len(b64_normal)}):")
        print(b64_normal[:50] + "...")
        
        # Inverted samples
        # Invert RGB: 255 - value
        inverted_samples = bytearray([255 - b for b in samples])
        compressed_inv = zlib.compress(inverted_samples)
        b64_inverted = base64.b64encode(compressed_inv).decode('utf-8')
        
        print(f"Inverted Base64 (len={len(b64_inverted)}):")
        print(b64_inverted[:50] + "...")
        
        # Save to file for easy reading
        with open("logo_assets.py", "w") as f:
            f.write(f'LOGO_WIDTH = {width}\n')
            f.write(f'LOGO_HEIGHT = {height}\n')
            f.write(f'LOGO_DATA_NORMAL = "{b64_normal}"\n')
            f.write(f'LOGO_DATA_INVERTED = "{b64_inverted}"\n')
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_image("lunartech_logo.png")
