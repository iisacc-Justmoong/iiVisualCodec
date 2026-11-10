"""Exercise installed vision contracts and the example in one disposable workspace."""
from pathlib import Path
import subprocess
import sys

contract, example, work = sys.argv[1:]
root = Path(work)
subprocess.run([contract, str(root)], check=True)
subprocess.run([example, str(root / "red.png"), str(root / "gray.png")], check=True)
