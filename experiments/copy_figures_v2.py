"""Copy figures and check."""
import shutil
from pathlib import Path

src = Path("D:/新论文/实验/results/figures")
dst = Path("D:/新论文/论文/figures")
dst.mkdir(parents=True, exist_ok=True)

print(f"Source exists: {src.exists()}")
print(f"Source contents:")
for f in src.glob("*"):
    print(f"  {f.name} ({f.stat().st_size} bytes)")

print(f"\nCopying to {dst}...")
copied = 0
for f in src.glob("*.png"):
    target = dst / f.name
    shutil.copy(f, target)
    copied += 1
    print(f"  Copied: {f.name}")

print(f"\nTotal copied: {copied}")
print(f"\nDestination contents:")
for f in dst.glob("*"):
    print(f"  {f.name} ({f.stat().st_size} bytes)")
