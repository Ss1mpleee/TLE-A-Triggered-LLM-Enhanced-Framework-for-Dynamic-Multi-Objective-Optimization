"""Find all result files."""
from pathlib import Path

candidates = [
    Path("D:/新论文/实验/results"),
    Path("D:/新论文/实验/实验/results"),
    Path("D:/新论文/实验/results/raw"),
    Path("D:/新论文/实验/实验/results/raw"),
]

for p in candidates:
    if p.exists():
        print(f"{p}: exists")
        for f in p.iterdir():
            print(f"  {f.name} ({f.stat().st_size} bytes)")
    else:
        print(f"{p}: NOT FOUND")
    print()
