"""A static codec package must reject a consumer's incompatible JPEG ABI."""
from pathlib import Path
import subprocess
import sys

cmake, config_path, expected, work = sys.argv[1:]
root = Path(work)
package = root / "lib/cmake/iiVisualCodec"
modules = root / "modules"
webp = root / "lib/cmake/WebP"
for directory in (package, modules, webp):
    directory.mkdir(parents=True)
# Script mode cannot create imported library targets. The package's dependency
# discovery runs before this aggregate target is declared.
config = Path(config_path).read_text().split('if(NOT TARGET iiVisualCodec::iiVisualCodec)')[0]
(package / "iiVisualCodecConfig.cmake").write_text(config + '\ncheck_required_components(iiVisualCodec)\n')
(package / "iiVisualCodecImageTargets.cmake").write_text("")
for name in ("PNG", "ZLIB", "TIFF"):
    (modules / f"Find{name}.cmake").write_text(f"set({name}_FOUND TRUE)\n")
(modules / "FindJPEG.cmake").write_text(
    "set(JPEG_VERSION ${TEST_JPEG_VERSION})\n"
    "include(FindPackageHandleStandardArgs)\n"
    "find_package_handle_standard_args(JPEG REQUIRED_VARS JPEG_VERSION VERSION_VAR JPEG_VERSION)\n")
(webp / "WebPConfig.cmake").write_text("set(WebP_FOUND TRUE)\n")
(webp / "WebPConfigVersion.cmake").write_text(
    'set(PACKAGE_VERSION "1.0")\nset(PACKAGE_VERSION_COMPATIBLE TRUE)\n')
script = root / "consumer.cmake"
script.write_text(
    f'set(CMAKE_MODULE_PATH "{modules}")\n'
    f'set(CMAKE_PREFIX_PATH "{root}")\n'
    'find_package(JPEG REQUIRED)\n'
    'find_package(iiVisualCodec CONFIG REQUIRED COMPONENTS Image)\n')
def probe(version):
    return subprocess.run([cmake, f"-DTEST_JPEG_VERSION={version}", "-P", str(script)],
                          text=True, capture_output=True)
matching = probe(expected)
assert matching.returncode == 0, matching.stdout + matching.stderr
mismatch = probe("80" if expected != "80" else "62")
assert mismatch.returncode != 0, "Static codec accepted an incompatible JPEG ABI"
assert "JPEG" in mismatch.stderr, mismatch.stdout + mismatch.stderr
