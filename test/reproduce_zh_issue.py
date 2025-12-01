import os
import subprocess
from pathlib import Path

# Configuration
INPUT_FILE = Path("/Users/vaheaslanyan/Documents/Apps/babel/test/input/fractured glass, failing cameras.pdf")
OUTPUT_DIR = Path("reproduce_output")
BABELDOC_DIR = Path("../handex-backend-antigravity/BabelDOC-main")
# Load API Key from .env (prioritize over env var to ensure new key is used)
env_path = Path(__file__).parent.parent / "handex-backend-antigravity" / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.strip().split("=", 1)[1]
                break


# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_translation(lang_code):
    print(f"\nTesting translation for {lang_code}...")
    
    cmd = [
        "uv", "run", "babeldoc",
        "--files", str(INPUT_FILE.absolute()),
        "--lang-out", lang_code,
        "--openai",
        "--openai-model", "gpt-4o",
        # Add API key if in env
    ]
    if "OPENAI_API_KEY" in os.environ:
        cmd.extend(["--openai-api-key", os.environ["OPENAI_API_KEY"]])
    cmd.extend(["--output", str(OUTPUT_DIR.absolute())])
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(BABELDOC_DIR.absolute()),
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
        
        print(f"Return code: {return_code}")
        if return_code != 0:
            stderr = process.stderr.read()
            print(f"STDERR:\n{stderr}")
        
        # Check for output file
        input_stem = INPUT_FILE.stem
        mono_pattern = f"{input_stem}.{lang_code}.mono.pdf"
        dual_pattern = f"{input_stem}.{lang_code}.dual.pdf"
        
        mono_file = OUTPUT_DIR / mono_pattern
        dual_file = OUTPUT_DIR / dual_pattern
        
        if mono_file.exists():
            print(f"✅ Output file created: {mono_file.name} ({mono_file.stat().st_size} bytes)")
        elif dual_file.exists():
            print(f"✅ Output file created: {dual_file.name} ({dual_file.stat().st_size} bytes)")
        else:
            print(f"❌ No output file created for {lang_code}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    # Test with fr
    run_translation("fr")
