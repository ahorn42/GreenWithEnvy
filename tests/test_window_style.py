import unittest

from gwe.util.window_style import resolve_use_header_bar, is_header_bar_desktop, InvalidWindowStyleError


class DesktopDetectionTest(unittest.TestCase):
    def test_header_bar_desktops(self):
        for desktop in ('GNOME', 'ubuntu:GNOME', 'Budgie:GNOME', 'Pantheon', 'gnome'):
            self.assertTrue(is_header_bar_desktop(desktop), desktop)

    def test_other_desktops_use_classic_title_bar(self):
        for desktop in ('KDE', 'X-Cinnamon', 'XFCE', 'LXQt', 'MATE', 'sway'):
            self.assertFalse(is_header_bar_desktop(desktop), desktop)

    def test_unknown_desktop_keeps_the_default(self):
        self.assertTrue(is_header_bar_desktop(''))


class ResolveUseHeaderBarTest(unittest.TestCase):
    def test_auto_detection(self):
        self.assertFalse(resolve_use_header_bar({'XDG_CURRENT_DESKTOP': 'KDE'}, ['gwe']))
        self.assertTrue(resolve_use_header_bar({'XDG_CURRENT_DESKTOP': 'ubuntu:GNOME'}, ['gwe']))
        self.assertTrue(resolve_use_header_bar({}, ['gwe']))

    def test_env_var_beats_detection(self):
        self.assertTrue(resolve_use_header_bar({'XDG_CURRENT_DESKTOP': 'KDE', 'GWE_HEADER_BAR': '1'}, ['gwe']))
        self.assertFalse(resolve_use_header_bar({'XDG_CURRENT_DESKTOP': 'GNOME', 'GWE_HEADER_BAR': 'off'}, ['gwe']))
        self.assertFalse(resolve_use_header_bar({'XDG_CURRENT_DESKTOP': 'KDE', 'GWE_HEADER_BAR': 'auto'}, ['gwe']))

    def test_cli_beats_env_var_and_last_one_wins(self):
        env = {'XDG_CURRENT_DESKTOP': 'KDE', 'GWE_HEADER_BAR': '0'}
        self.assertTrue(resolve_use_header_bar(env, ['gwe', '--header-bar']))
        self.assertFalse(resolve_use_header_bar({'GWE_HEADER_BAR': '1'}, ['gwe', '--no-header-bar']))
        self.assertFalse(resolve_use_header_bar({}, ['gwe', '--header-bar', '--no-header-bar']))

    def test_options_after_double_dash_are_ignored(self):
        self.assertFalse(resolve_use_header_bar({'XDG_CURRENT_DESKTOP': 'KDE'}, ['gwe', '--', '--header-bar']))

    def test_invalid_env_var(self):
        with self.assertRaises(InvalidWindowStyleError):
            resolve_use_header_bar({'GWE_HEADER_BAR': 'maybe'}, ['gwe'])


if __name__ == '__main__':
    unittest.main()
