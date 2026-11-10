"""Check installation defaults without downloading or installing anything."""
from pathlib import Path
import os
import subprocess
import sys

sys.path.insert(0, sys.argv[2])
import ii_file_provider as provider
project = Path(__file__).resolve().parents[1]
owner = Path(sys.argv[3]).resolve()
cmake = sys.argv[1]
home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
assert home
def probe(name, override=None):
    source = owner / name
    provider.mkdir(source, parents=True, exist_ok=False)
    content = ("cmake_minimum_required(VERSION 3.24)\nproject(Prefix NONE)\n"
               + 'include("' + str(project / "cmake/InstallPrefix.cmake") + '")\n'
               + "visual_set_install_prefix()\n")
    provider.write_text(source / "CMakeLists.txt", content)
    command = [cmake, "-S", str(source), "-B", str(source / "build")]
    if override is not None: command.append("-DCMAKE_INSTALL_PREFIX=" + str(override))
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    cache = (source / "build/CMakeCache.txt").read_text()
    expected = override or Path(home) / ".local/SDK/iiVisualCodec"
    assert "CMAKE_INSTALL_PREFIX:PATH=" + str(expected) in cache
probe("default")
probe("explicit", owner / "custom prefix")

bin_dir = owner / "bin"
provider.mkdir(bin_dir, exist_ok=False)
for name in ("cmake", "ctest", "python3"):
    script = bin_dir / name
    provider.write_text(script, "#!/bin/sh\nprintf '" + name + ":'\nprintf ' <%s>' \"$@\"\nprintf '\\n'\n")
    script.chmod(0o700)
env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + "/usr/bin:/bin")
env.pop("IIVISUALCODEC_BOOTSTRAP", None)
env.pop("IISDK_NATIVE_PREFIX", None)
def script_run():
    result = subprocess.run(["/bin/bash", str(project / "install-native.sh")],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout
text = script_run()
assert "python3:" not in text
assert "<-DCMAKE_INSTALL_PREFIX=" + str(Path(home) / ".local/SDK/iiVisualCodec") + ">" in text
assert str(project / "resources/dependencies/prefix") in text
env["IISDK_NATIVE_PREFIX"] = str(owner / "custom prefix")
env["IIVISUALCODEC_BOOTSTRAP"] = "1"
text = script_run()
assert "python3:" in text and "bootstrap_dependencies.py" in text
assert "<-DCMAKE_INSTALL_PREFIX=" + env["IISDK_NATIVE_PREFIX"] + ">" in text
