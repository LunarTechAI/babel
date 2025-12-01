import os
import shutil
import subprocess
import time
from pathlib import Path

# Configuration
INPUT_FILE = Path("input/fractured glass, failing cameras.pdf")
OUTPUT_DIR = Path("output")
BABELDOC_DIR = Path("../handex-backend-antigravity/BabelDOC-main")

# Unique title generation
timestamp = int(time.time())
UNIQUE_FILENAME = f"fractured_glass_watermark_test_{timestamp}.pdf"
TEMP_INPUT_FILE = INPUT_FILE.parent / UNIQUE_FILENAME

# Load API Key from .env
env_path = Path(__file__).parent.parent / "handex-backend-antigravity" / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.strip().split("=", 1)[1]
                break

def run_translation():
    print(f"Preparing to translate with unique title: {UNIQUE_FILENAME}")
    
    # Copy input file to new unique name
    shutil.copy(INPUT_FILE, TEMP_INPUT_FILE)
    print(f"Created temporary input file: {TEMP_INPUT_FILE}")
    
    cmd = [
        "uv", "run", "babeldoc",
        "--files", str(TEMP_INPUT_FILE.absolute()),
        "--lang-out", "fr",
        "--openai",
        "--openai-model", "gpt-4o",
        "--output", str(OUTPUT_DIR.absolute())
    ]
    
    if "OPENAI_API_KEY" in os.environ:
        cmd.extend(["--openai-api-key", os.environ["OPENAI_API_KEY"]])
    
    try:
        print("Starting translation...")
        with open("translation.log", "w") as log_file:
            process = subprocess.Popen(
                cmd,
                cwd=str(BABELDOC_DIR.absolute()),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr to stdout
                text=True
            )
            
            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"  {output.strip()}")
                    log_file.write(output)
                    
        return_code = process.poll()
        
        if return_code == 0:
            print("✅ Translation successful")
            
            # Find the output file
            output_files = list(OUTPUT_DIR.glob(f"{TEMP_INPUT_FILE.stem}*.fr.mono.pdf"))
            if output_files:
                # Sort by modification time to get the latest
                output_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                latest_output = output_files[0]
                print(f"Output file found: {latest_output}")
                
                # Post-processing: Add Logo and Link
                try:
                    print("Applying smart logo watermark and hyperlink...")
                    import fitz
                    
                    doc = fitz.open(latest_output)
                    logo_path = BABELDOC_DIR.parent / "lunartech_logo.png"
                    
                    if not logo_path.exists():
                        print(f"❌ Logo file not found at {logo_path}")
                    else:
                        for page in doc:
                            page_width = page.rect.width
                            page_height = page.rect.height
                            
                            # Logo dimensions and position
                            # Target width: 20% of page width
                            target_width = page_width * 0.2
                            
                            # Get logo aspect ratio
                            img = fitz.open(logo_path)
                            logo_width_orig = img[0].rect.width
                            logo_height_orig = img[0].rect.height
                            scale = target_width / logo_width_orig
                            target_height = logo_height_orig * scale
                            
                            margin_x = page_width * 0.05
                            margin_y = page_height * 0.05
                            
                            # Bottom right position (PDF coordinates: y increases downwards in pymupdf rect?)
                            # PyMuPDF Rect: (x0, y0, x1, y1). (0,0) is top-left usually.
                            # Let's verify coordinate system.
                            # Standard PDF: (0,0) bottom-left.
                            # PyMuPDF: (0,0) top-left.
                            
                            logo_x0 = page_width - margin_x - target_width
                            logo_y0 = page_height - margin_y - target_height
                            logo_x1 = logo_x0 + target_width
                            logo_y1 = logo_y0 + target_height
                            
                            logo_rect = fitz.Rect(logo_x0, logo_y0, logo_x1, logo_y1)
                            
                            # Check background color for smart logo (simple heuristic)
                            # Sample center pixel? PyMuPDF pixmap.
                            # For now, default to normal logo. Inverting needs image processing.
                            # Let's just insert the normal logo for now to ensure it works.
                            # If we want smart logo, we can check pixmap at logo center.
                            
                            # Insert Image
                            page.insert_image(logo_rect, filename=str(logo_path))
                            
                            # Insert Link
                            page.insert_link({
                                "kind": fitz.LINK_URI,
                                "from": logo_rect,
                                "uri": "https://lunartech.ai"
                            })
                            
                        # Save to a new file
                        final_output = latest_output.with_name(latest_output.stem + ".watermarked.pdf")
                        doc.save(final_output)
                        print(f"✅ Watermarked PDF saved to: {final_output}")
                        
                except Exception as e:
                    print(f"❌ Failed to apply watermark: {e}")
                    import traceback
                    traceback.print_exc()

            else:
                print(f"❌ Output file not found at expected path: {OUTPUT_DIR}/{TEMP_INPUT_FILE.stem}*.fr.mono.pdf")
        else:
            stderr = process.stderr.read()
            print(f"❌ Translation failed with code {return_code}")
            print(f"STDERR:\n{stderr}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    finally:
        # Cleanup temporary input file
        if TEMP_INPUT_FILE.exists():
            TEMP_INPUT_FILE.unlink()
            print(f"Cleaned up temporary file: {TEMP_INPUT_FILE}")

if __name__ == "__main__":
    run_translation()
