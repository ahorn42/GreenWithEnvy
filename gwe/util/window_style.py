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
"""Whether the windows use a GNOME style header bar or a classic title bar with a toolbar.

The header bar is the typical GNOME look and looks out of place on other desktops like KDE Plasma, where the title bar
is drawn by the window manager. By default it is used only on the desktops that are designed around it, but it can be
forced with ``--header-bar`` / ``--no-header-bar`` or the ``GWE_HEADER_BAR`` environment variable (1/0/auto).
This module has no dependency on Gtk, so the decision can be taken (and its errors reported) before the UI is created.
"""
import os
import sys
from typing import Mapping, Optional, Sequence

HEADER_BAR_ENV_VAR = 'GWE_HEADER_BAR'
HEADER_BAR_CLI_OPTION = 'header-bar'
NO_HEADER_BAR_CLI_OPTION = 'no-header-bar'

# Desktops (XDG_CURRENT_DESKTOP) that are designed around the header bar
_HEADER_BAR_DESKTOPS = frozenset({'gnome', 'budgie', 'pantheon'})
_TRUE_VALUES = frozenset({'1', 'true', 'yes', 'on'})
_FALSE_VALUES = frozenset({'0', 'false', 'no', 'off'})

_use_header_bar: Optional[bool] = None


class InvalidWindowStyleError(ValueError):
    pass


def is_header_bar_desktop(xdg_current_desktop: str) -> bool:
    """XDG_CURRENT_DESKTOP is a colon separated list, e.g. "ubuntu:GNOME" or "KDE". Unknown desktop: keep the default."""
    desktops = {desktop.lower() for desktop in xdg_current_desktop.split(':') if desktop}
    return not desktops or bool(desktops & _HEADER_BAR_DESKTOPS)


def resolve_use_header_bar(env: Mapping[str, str], argv: Sequence[str]) -> bool:
    """The command line option (the last one wins) beats the environment variable, which beats the detection."""
    cli_value = None
    for arg in argv[1:]:
        if arg == '--':
            break
        if arg == '--' + HEADER_BAR_CLI_OPTION:
            cli_value = True
        elif arg == '--' + NO_HEADER_BAR_CLI_OPTION:
            cli_value = False
    if cli_value is not None:
        return cli_value
    env_value = env.get(HEADER_BAR_ENV_VAR, '').strip().lower()
    if env_value in _TRUE_VALUES:
        return True
    if env_value in _FALSE_VALUES:
        return False
    if env_value not in ('', 'auto'):
        raise InvalidWindowStyleError(
            f"Invalid value {env_value!r} for the environment variable {HEADER_BAR_ENV_VAR}: expected 1, 0 or auto")
    return is_header_bar_desktop(env.get('XDG_CURRENT_DESKTOP', ''))


def use_header_bar() -> bool:
    global _use_header_bar  # pylint: disable=global-statement
    if _use_header_bar is None:
        _use_header_bar = resolve_use_header_bar(os.environ, sys.argv)
    return _use_header_bar


def init_window_style() -> None:
    """Resolve the style right away so that an invalid value is reported as a clean error message."""
    try:
        use_header_bar()
    except InvalidWindowStyleError as e:
        print(f"gwe: error: {e}", file=sys.stderr)
        sys.exit(2)
