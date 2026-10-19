#!/usr/bin/env python3
"""Stage public site files, excluding scripts, local drafts, and repository state."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = [
    "index.html", "korean.html", "english.html", "serving.html", "papers.html",
    "styles.css", "papers.css", "app.js", "landing.js", "serving.js", "papers.js",
    "english-copy.js", "inventory-data.js", "serving-data.js", "site-meta.js", "updates.json",
    "korean_benchmark_inventory.csv", "english_benchmark_inventory.csv", "serving_inventory.csv",
    "benchmark_top_models.csv", "serving_reference_values.csv",
]


def main():
    destination = ROOT / "_site"
    destination.mkdir(exist_ok=False)
    assets = subprocess.check_output(["git", "ls-files", "-z", "assets"], cwd=ROOT).decode().split("\0")
    for name in PUBLIC + [name for name in assets if name]:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    print(f"Staged site in {destination}")


if __name__ == "__main__":
    main()
