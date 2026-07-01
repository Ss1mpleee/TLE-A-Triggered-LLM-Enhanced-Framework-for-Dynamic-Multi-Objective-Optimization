from pathlib import Path
import shutil

# Check both possible paths
paths = [
    Path("D:/新论文/实验/results/figures"),
    Path("D:/新论文/实验/实验/results/figures"),
]
for p in paths:
    print(f"{p}: exists={p.exists()}")
    if p.exists():
        for f in p.glob("*.png"):
            print(f"  {f.name} ({f.stat().st_size} bytes)")

# Real source dir
real_src = Path("D:/新论文/实验/results/figures")
dst = Path("D:/新论文/论文/figures")
dst.mkdir(parents=True, exist_ok=True)

if real_src.exists():
    print(f"\nCopying from {real_src} to {dst}")
    for f in real_src.glob("*"):
        if f.suffix.lower() in ('.png', '.jpg', '.pdf'):
            shutil.copy(f, dst / f.name)
            print(f"  Copied: {f.name}")
else:
    print(f"\n{real_src} does not exist!")
    # Search filesystem for the figures
    print("Searching for figures...")
    candidates = list(Path("D:/").glob("**/tle_architecture.png"))
    for c in candidates:
        print(f"  Found: {c}")
