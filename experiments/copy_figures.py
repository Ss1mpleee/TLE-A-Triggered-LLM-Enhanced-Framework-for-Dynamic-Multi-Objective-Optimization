import shutil
from pathlib import Path

src = Path("D:/新论文/实验/results/figures")
dst = Path("D:/新论文/论文/figures")
dst.mkdir(parents=True, exist_ok=True)

if not src.exists():
    print(f"Source not found: {src}")
else:
    for f in src.glob("*.png"):
        target = dst / f.name
        shutil.copy(f, target)
        print(f"Copied: {f.name} -> {target}")

print("\nFinal figures:")
for f in dst.glob("*.png"):
    print(f"  {f.name} ({f.stat().st_size} bytes)")
