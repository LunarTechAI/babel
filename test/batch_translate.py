import os
import subprocess
import time
from pathlib import Path

# Configuration
INPUT_FILE = Path("/Users/vaheaslanyan/Documents/Apps/babel/test/input/fractured glass, failing cameras.pdf")
OUTPUT_DIR = Path("/Users/vaheaslanyan/Documents/Apps/babel/test/output")
BABELDOC_DIR = Path("/Users/vaheaslanyan/Documents/Apps/babel/handex-backend-antigravity/BabelDOC-main")

# Load API Key from .env (prioritize over env var to ensure new key is used)
env_path = Path(__file__).parent.parent / "handex-backend-antigravity" / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.strip().split("=", 1)[1]
                print(f"Loaded API key from .env: ...{os.environ['OPENAI_API_KEY'][-4:]}")
                break

# Languages mapping (Name -> Code)
LANGUAGES = {
    "English": "en",
    "Chinese": "zh-CN",
    "Hindi": "hi",
    "Arabic": "ar",
    "Russian": "ru",
    "Armenian": "hy",
    "Japanese": "ja",
    "German": "de",
    "Dutch": "nl",
    "Italian": "it",
    "French": "fr",
    "Spanish": "es",
    "Portuguese": "pt",
    "Korean": "ko",
    "Turkish": "tr",
    "Polish": "pl",
    "Vietnamese": "vi",
    "Ukrainian": "uk",
    "Romanian": "ro",
    "Thai": "th",
    "Javanese": "jv",
    "Punjabi": "pa"
}

def run_translation(lang_name, lang_code):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting translation for {lang_name} ({lang_code})...")
    
    cmd = [
        "uv", "run", "babeldoc",
        "--files", str(INPUT_FILE),
        "--lang-out", lang_code,
        "--openai",
        "--openai-model", "gpt-4o",
        "--pool-max-workers", "4",
        "--output", str(OUTPUT_DIR)
    ]
    
    # Add API key if in env, otherwise assume it's set in shell
    if "OPENAI_API_KEY" in os.environ:
        cmd.extend(["--openai-api-key", os.environ["OPENAI_API_KEY"]])
    
    try:
        # Run BabelDOC
        process = subprocess.Popen(
            cmd,
            cwd=str(BABELDOC_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Stream output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"  {output.strip()}")
                
        return_code = process.poll()
        
        if return_code == 0:
            print(f"✅ Successfully translated to {lang_name}")
            return True
        else:
            stderr = process.stderr.read()
            print(f"❌ Failed to translate to {lang_name}")
            print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during translation to {lang_name}: {str(e)}")
        return False

def main():
    from datetime import datetime
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting batch translation for {len(LANGUAGES)} languages")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_DIR}")
    
    successful = []
    failed = []
    
    for lang_name, lang_code in LANGUAGES.items():
        if run_translation(lang_name, lang_code):
            successful.append(lang_name)
        else:
            failed.append(lang_name)
            
    print("\n" + "="*50)
    print("Batch Translation Summary")
    print("="*50)
    print(f"Total: {len(LANGUAGES)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed languages:")
        for lang in failed:
            print(f"- {lang}")

if __name__ == "__main__":
    from datetime import datetime
    main()
