import os
import zipfile
from pathlib import Path

def build_zip():
    zip_filename = "n100_financial_intelligence_platform_submission.zip"
    print(f"Building clean project submission ZIP: {zip_filename}...")
    
    # Define what is allowed
    allowed_dirs = ["src", "tests", "config", "notebooks", "data", "output", "reports", "docs"]
    allowed_files = ["README.md", "requirements.txt", "Makefile"]
    
    # Excluded extensions and patterns
    excluded_extensions = {".pyc", ".log"}
    excluded_names = {".env", "credentials", "secrets", "__pycache__", ".git", ".venv", "scratch"}
    
    count_files = 0
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the root directories
        for root, dirs, files in os.walk("."):
            # Exclude folders dynamically in-place to avoid descending into them
            dirs[:] = [d for d in dirs if d not in excluded_names]
            
            # Get path relative to the workspace root
            rel_path = Path(root).relative_to(Path("."))
            
            # Determine if this directory path belongs to an allowed directory
            parts = rel_path.parts
            if not parts:
                # We are at the root level, only package allowed files
                for f in files:
                    if f in allowed_files:
                        file_path = Path(root) / f
                        zipf.write(file_path, arcname=str(file_path))
                        print(f"  [+] Packaged: {file_path}")
                        count_files += 1
            else:
                # Check if top-level parent folder is allowed
                if parts[0] in allowed_dirs:
                    for f in files:
                        file_path = Path(root) / f
                        # Double-check exclusions
                        if file_path.suffix in excluded_extensions:
                            continue
                        if any(x in file_path.parts for x in excluded_names):
                            continue
                        if any(x in file_path.name.lower() for x in ["credentials", "secrets", ".env"]):
                            continue
                        
                        # Add to ZIP
                        zipf.write(file_path, arcname=str(file_path))
                        count_files += 1
                        
    print(f"\nZIP building complete. Successfully packaged {count_files} files in {zip_filename}.")

if __name__ == "__main__":
    build_zip()
