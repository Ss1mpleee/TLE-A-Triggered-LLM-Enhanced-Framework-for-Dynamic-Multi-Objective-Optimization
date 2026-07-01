"""Copy results from double-nested location to the correct single location."""
import shutil
from pathlib import Path

# Double-nested (where they actually are)
double_raw = Path("D:/新论文/实验/实验/results/raw")
double_fig = Path("D:/新论文/实验/实验/results/figures")

# Correct single-nested location
correct_raw = Path("D:/新论文/实验/results/raw")
correct_fig = Path("D:/新论文/实验/results/figures")

correct_raw.mkdir(parents=True, exist_ok=True)
correct_fig.mkdir(parents=True, exist_ok=True)

# Copy raw JSON files
print("Copying raw JSON files...")
for f in double_raw.glob("*.json"):
    target = correct_raw / f.name
    shutil.copy(f, target)
    print(f"  {f.name} -> {target}")

# Copy figures
print("\nCopying figures...")
for f in double_fig.glob("*.png"):
    target = correct_fig / f.name
    shutil.copy(f, target)
    print(f"  {f.name} -> {target}")

print("\nDone. Final locations:")
print(f"  Raw: {correct_raw}")
print(f"  Figures: {correct_fig}")
print(f"  Paper figures: D:/新论文/论文/figures/")
