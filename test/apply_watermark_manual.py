import os
import sys
import shutil
import logging
from pathlib import Path
import pymupdf

# Mocking classes
class TranslationConfig:
    def __init__(self, input_file):
        self.input_file = input_file
        self.working_dir = Path(input_file).parent

    def get_working_file_path(self, filename):
        return self.working_dir / filename

class TranslateResult:
    def __init__(self, mono_pdf_path, dual_pdf_path=None, auto_extracted_glossary_path=None):
        self.mono_pdf_path = mono_pdf_path
        self.dual_pdf_path = dual_pdf_path
        self.auto_extracted_glossary_path = auto_extracted_glossary_path

# Mock logger
logger = logging.getLogger("test")
logging.basicConfig(level=logging.INFO)

def safe_save(doc, path):
    doc.save(path)

# Copy of the function to be tested
def add_watermark(
    translate_result: TranslateResult, translate_config: TranslationConfig
):
    """Add logo watermark to the output PDFs."""
    processed = []
    
    # Define assets path
    assets_dir = Path("/Users/vaheaslanyan/Documents/Apps/babel/assets")
    black_logo_path = assets_dir / "Horizontal Black_1@4x.png"
    white_logo_path = assets_dir / "Horizontal White_1@4x.png"
    
    if not black_logo_path.exists() or not white_logo_path.exists():
        logger.warning(f"Watermark assets not found at {assets_dir}, skipping watermark.")
        return

    for attr in (
        "mono_pdf_path",
        "dual_pdf_path",
    ):
        path = getattr(translate_result, attr)
        if not path or path in processed:
            continue
        processed.append(path)

        try:
            temp_path = translate_config.get_working_file_path(f"{path.stem}.watermark.pdf")
            pdf = pymupdf.open(path)
            
            for page in pdf:
                # Determine background color at bottom right
                page_rect = page.rect
                margin_x = 20
                margin_y = 20
                wm_width = 100 
                wm_height = 30 
                
                # Position: Bottom Right
                rect = pymupdf.Rect(
                    page_rect.width - wm_width - margin_x,
                    page_rect.height - wm_height - margin_y,
                    page_rect.width - margin_x,
                    page_rect.height - margin_y
                )
                
                # Sample background color
                sample_point = pymupdf.Point(rect.x0 + rect.width/2, rect.y0 + rect.height/2)
                
                pix = page.get_pixmap(clip=pymupdf.Rect(sample_point.x - 5, sample_point.y - 5, sample_point.x + 5, sample_point.y + 5))
                
                # Calculate average luminance
                if pix.n >= 3:
                    pixels = list(pix.samples)
                    r_sum = 0
                    g_sum = 0
                    b_sum = 0
                    count = 0
                    step = pix.n
                    for i in range(0, len(pixels), step):
                        r_sum += pixels[i]
                        g_sum += pixels[i+1]
                        b_sum += pixels[i+2]
                        count += 1
                    
                    if count > 0:
                        avg_r = r_sum / count
                        avg_g = g_sum / count
                        avg_b = b_sum / count
                        luminance = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b
                    else:
                        luminance = 255 
                else:
                    luminance = 255 
                
                if luminance < 128:
                    logo_path = str(white_logo_path)
                    print(f"Page {page.number}: Dark background detected ({luminance:.2f}), using White Logo")
                else:
                    logo_path = str(black_logo_path)
                    print(f"Page {page.number}: Light background detected ({luminance:.2f}), using Black Logo")
                
                # Insert Image
                page.insert_image(rect, filename=logo_path)
                
                # Add Hyperlink
                page.insert_link({
                    "kind": pymupdf.LINK_URI,
                    "from": rect,
                    "uri": "https://lunartech.ai"
                })

            safe_save(pdf, temp_path)
            # For this test, we won't overwrite the original, but keep the temp file as output
            # shutil.move(temp_path, path) 
            print(f"Watermarked PDF saved to: {temp_path}")
            
        except Exception as e:
            logger.error(f"Failed to add watermark to {path}: {e}")
            import traceback
            traceback.print_exc()

def run_test():
    target_file = Path("/Users/vaheaslanyan/Documents/Apps/babel/test/output/fractured glass, failing cameras.en.mono.pdf")
    
    if not target_file.exists():
        print(f"File not found: {target_file}")
        return

    config = TranslationConfig(input_file=str(target_file))
    result = TranslateResult(mono_pdf_path=target_file)

    print(f"Applying watermark to {target_file}...")
    add_watermark(result, config)

if __name__ == "__main__":
    run_test()
