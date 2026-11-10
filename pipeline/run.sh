#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export LD_LIBRARY_PATH=/nix/store/604gsr59rj7dzd0nrhp143rpvf7gyiaz-gcc-15.3.0-lib/lib:/nix/store/6ghariqqf33l5xqn7alx58dys7kz2wm5-zlib-1.3.1/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
exec ../.venv/bin/python "$@"
