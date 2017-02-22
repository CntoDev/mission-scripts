# CNTO Mission-related scripts

## `mission_shipper.py`

This script exists to allow us to automatically generate the `@cnto_missions`
ArmA3 Mod in order to ship large missions (>5MB) to our players using our
already-existing mod distribution system.

Missions are to be deposited in a defined `missions-path` directory (default:
`./missions`) and will be automatically packaged in the final `mission.pbo`.

Missions need to be in their original format, exported missions (`.pbo` files)
are not supported.

When the process ends, a `@cnto_missions` mod directory will be created in the
`target-path` directory (default: current directory), which can be in turn
uploaded in the mod repository.

**Note**: *Binarized `mission.sqm` files are currently not supported*

### Requirements

* Tested for Linux. Windows usage is at your own risk.
* depbo-tools 0.6.02 (https://dev.withsix.com/projects/mikero-pbodll/files)
* Python 3, tested under 3.6, in production under 3.4, but 3.2+ should work.
* Python libraries defined in `requirements.txt`

### Usage

```
usage: mission_shipper.py [-h] [--template-path TEMPLATE_PATH]
                          [--missions-path MISSIONS_PATH]
                          [--build-path BUILD_PATH]
                          [--target-path TARGET_PATH]

Helper script for generating the @cnto_missions mod.

optional arguments:
  -h, --help            show this help message and exit
  --template-path TEMPLATE_PATH
                        Source directory that contains the template files
  --missions-path MISSIONS_PATH
                        Source directory for non-pboized missions to package.
  --build-path BUILD_PATH
                        Build directory for storing the mod before pobization.
  --target-path TARGET_PATH
                        Target directory for storing the generated
                        @cnto_missions mod.
```

Sane defaults are in use and as such regular usage could be limited to:

```
$> ./mission_shipper.py
```

If your `depbo-tools` binaries is not in your `PATH`, you may explicit the path to
`makepbo` through the `MAKEPBO_PATH` environment variable:

```
$> MAKEPBO_PATH=/home/user/depbo-tools-0.6.02/bin/makepbo ./mission_shipper.py
```

You might also need to help `makepbo` finding the `libdepbo.so` shared library:

```
$> LD_PRELOAD=/home/user/depbo-tools-0.6.02/lib/libdepbo.so.0 ./mission_shipper.py
```
