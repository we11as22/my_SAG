"""
Download NLTK data locally to project directory

Run once on development machine to download NLTK data to project's nltk_data/ directory
Then commit to git, Docker build will directly COPY, avoiding network download on each build

Usage:
    python scripts/download_nltk_data.py
"""

import ssl
import sys
from pathlib import Path

def download_nltk_to_project():
    """Download NLTK data to project directory"""
    try:
        import nltk
    except ImportError:
        print("❌ Error: nltk library not installed")
        print("Please install first: pip install nltk")
        sys.exit(1)
    
    # Project root directory
    project_root = Path(__file__).parent.parent
    nltk_data_dir = project_root / "nltk_data"
    nltk_data_dir.mkdir(exist_ok=True)
    
    print("="*60)
    print("SAG - NLTK Data Local Download Tool")
    print("="*60)
    print(f"\n📁 Download directory: {nltk_data_dir}")
    
    # Handle SSL certificate issues
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # Required resources list
    resources = ['punkt', 'punkt_tab']
    
    print("\nStarting NLTK data download...")
    success_count = 0
    
    for resource in resources:
        print(f"\n📥 Downloading {resource}...")
        try:
            nltk.download(resource, download_dir=str(nltk_data_dir), quiet=False)
            print(f"✓ {resource} download completed")
            success_count += 1
        except Exception as e:
            print(f"✗ {resource} download failed: {e}")
    
    # Verify
    print("\n" + "="*60)
    print("Verifying downloaded data...")
    print("="*60)
    
    # Temporarily add to NLTK search path
    if str(nltk_data_dir) not in nltk.data.path:
        nltk.data.path.insert(0, str(nltk_data_dir))
    
    all_ok = True
    for resource in resources:
        resource_path = {
            'punkt': 'tokenizers/punkt',
            'punkt_tab': 'tokenizers/punkt_tab'
        }.get(resource, resource)
        
        try:
            path = nltk.data.find(resource_path)
            print(f"✓ {resource}: {path}")
        except Exception as e:
            print(f"✗ {resource} verification failed: {e}")
            all_ok = False
    
    # Summary
    print("\n" + "="*60)
    if all_ok and success_count == len(resources):
        print("✅ All NLTK data successfully downloaded to project directory!")
        print(f"\n📁 Location: {nltk_data_dir}")
        print(f"📦 Downloaded: {', '.join(resources)}")
        
        # Check directory size
        total_size = sum(f.stat().st_size for f in nltk_data_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"💾 Total size: {size_mb:.2f} MB")
        
        print("\nNext steps:")
        print("  1. Commit data to git:")
        print("     git add nltk_data/")
        print("     git commit -m 'Add pre-downloaded NLTK data'")
        print("     git push")
        print("\n  2. Rebuild Docker image:")
        print("     docker-compose build api")
    else:
        print("⚠️  Some resources download failed, please check network connection and retry")
        sys.exit(1)
    
    print("="*60)

if __name__ == "__main__":
    download_nltk_to_project()

