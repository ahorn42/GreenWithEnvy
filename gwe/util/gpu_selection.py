# This file is part of gwe.
#
# gwe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwe.  If not, see <http://www.gnu.org/licenses/>.
"""Selection of the GPU controlled by this GWE instance.

GWE controls exactly one GPU per running instance. To manage several GPUs, start one instance per GPU, e.g.
``gwe --gpu-index 1`` or ``GWE_GPU_INDEX=1 gwe``. The index must be resolved before the Gtk application and the
database are created, which is why this module has no dependency on Gtk or the rest of the app.
"""
import os
import re
import sys
from typing import Mapping, Optional, Sequence

GPU_INDEX_ENV_VAR = 'GWE_GPU_INDEX'
GPU_INDEX_CLI_OPTION = 'gpu-index'

_CLI_FLAG = '--' + GPU_INDEX_CLI_OPTION
_INDEX_PATTERN = re.compile(r'[0-9]+')

_selected_gpu_index: Optional[int] = None


class InvalidGpuIndexError(ValueError):
    pass


def parse_gpu_index(value: str, source: str) -> int:
    value = value.strip()
    if not _INDEX_PATTERN.fullmatch(value):
        raise InvalidGpuIndexError(f"Invalid GPU index {value!r} from {source}: expected a non-negative integer")
    return int(value)


def resolve_gpu_index(env: Mapping[str, str], argv: Sequence[str]) -> int:
    """Return the GPU index requested via ``--gpu-index`` (wins) or ``GWE_GPU_INDEX``, 0 if neither is set."""
    cli_value = None
    args = list(argv[1:])
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--':
            break
        if arg == _CLI_FLAG:
            if i + 1 >= len(args):
                raise InvalidGpuIndexError(f"Option {_CLI_FLAG} requires a value")
            cli_value = args[i + 1]
            i += 1
        elif arg.startswith(_CLI_FLAG + '='):
            cli_value = arg[len(_CLI_FLAG) + 1:]
        i += 1
    if cli_value is not None:
        return parse_gpu_index(cli_value, f"option {_CLI_FLAG}")
    env_value = env.get(GPU_INDEX_ENV_VAR, '').strip()
    if env_value:
        return parse_gpu_index(env_value, f"environment variable {GPU_INDEX_ENV_VAR}")
    return 0


def get_application_id(base_id: str, gpu_index: int) -> str:
    """Instances for different GPUs need different application ids, otherwise Gtk forwards the command line to the
    already running instance instead of starting a new one. GPU 0 keeps the original id."""
    return base_id if gpu_index == 0 else f"{base_id}.gpu{gpu_index}"


def get_database_name(base_name: str, gpu_index: int) -> str:
    """Every instance keeps its own profiles/settings. GPU 0 keeps the original file so existing data is preserved."""
    if gpu_index == 0:
        return base_name
    stem, dot, extension = base_name.rpartition('.')
    return f"{stem}-gpu{gpu_index}{dot}{extension}" if dot else f"{base_name}-gpu{gpu_index}"


def set_gpu_index(gpu_index: int) -> None:
    global _selected_gpu_index  # pylint: disable=global-statement
    _selected_gpu_index = gpu_index


def get_gpu_index() -> int:
    """The selected GPU index. It is resolved lazily from the environment and the command line on first use, because
    the peewee models bind the database (which is per GPU) while they are imported, i.e. before main() runs."""
    global _selected_gpu_index  # pylint: disable=global-statement
    if _selected_gpu_index is None:
        _selected_gpu_index = resolve_gpu_index(os.environ, sys.argv)
    return _selected_gpu_index


def init_gpu_index() -> None:
    """Resolve the GPU index right away so that an invalid value is reported as a clean error message."""
    try:
        get_gpu_index()
    except InvalidGpuIndexError as e:
        print(f"gwe: error: {e}", file=sys.stderr)
        sys.exit(2)
