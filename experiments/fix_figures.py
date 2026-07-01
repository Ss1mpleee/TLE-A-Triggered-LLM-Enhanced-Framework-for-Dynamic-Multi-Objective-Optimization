"""Copy figures from the doubled-path location to the correct paper location."""
import shutil
from pathlib import Path

# Source: where the figures actually are
src = Path("D:/新论文/实验/实验/results/figures")
# Target: where main.tex expects them
dst = Path("D:/新论文/论文/figures")
dst.mkdir(parents=True, exist_ok=True)

if not src.exists():
    print(f"Source {src} does not exist!")
else:
    print(f"Source: {src}")
    print(f"Destination: {dst}")
    for f in src.iterdir():
        if f.suffix.lower() in ('.png', '.jpg', '.pdf'):
            target = dst / f.name
            shutil.copy(f, target)
            print(f"  Copied: {f.name} ({f.stat().st_size} bytes)")

    print(f"\nFinal figures in {dst}:")
    for f in dst.iterdir():
        print(f"  {f.name} ({f.stat().st_size} bytes)")
