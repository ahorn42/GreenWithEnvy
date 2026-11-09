# GreenWithEnvy (GWE)
GWE is a GTK system utility designed to provide information, control the fans and overclock your NVIDIA video card
and graphics processor.

## 💡 Features
<img src="/data/icons/hicolor/48x48@2x/apps/com.leinardi.gwe.png" width="96" align="right" hspace="0" />

* Show general GPU stats (model name, driver version, gpu/memory/power usage, clocks, temps, etc)
* GPU and Memory overclock offset profiles
* Custom Fan curve profiles
* Change power limit
* Historical data graphs

<img src="/art/screenshot-1.png" width="800" align="middle"/>

## 📦 How to get GWE
If you don't like to reading manuals and/or you don't know what the Nvidia CoolBits are,
you can watch the following How To made by [Intelligent Gaming](https://www.youtube.com/channel/UCH4d4o0Otxa7BNYs5Z5UEjg):

[![How To Overclock And Control Fans On An nVidia Graphic Card In Linux - Green With Envy / GWE](https://img.youtube.com/vi/HAKe9ladLvc/0.jpg)](https://www.youtube.com/watch?v=HAKe9ladLvc)

### Install from Flathub
This is the preferred way to get GWE on any major distribution (Arch, Fedora, Linux Mint, openSUSE, Ubuntu, etc).

If you don't have Flatpak installed you can find step by step instructions [here](https://flatpak.org/setup/).

Make sure to have the Flathub remote added to the current user:

```bash
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

#### Install
```bash
flatpak --user install flathub com.leinardi.gwe
flatpak update # needed to be sure to have the latest org.freedesktop.Platform.GL.nvidia
```

#### Run
```bash
flatpak run com.leinardi.gwe
```
#### ⚠ Flatpak limitations
##### Beta Drivers
Currently [Flatpak does not support Nvidia Beta drivers](https://github.com/flathub/org.freedesktop.Platform.GL.nvidia/issues/1)
like 396.54.09 or 415.22.05.

##### Bumblebee and Optimus
Currently [Flatpak does not support Bumblebee](https://github.com/flatpak/flatpak/issues/869). If you want to use GWE with Bumblebee
you need to install it from the source code.

### Distro specific packages
#### Arch Linux
Install the `gwe` package from the AUR using your favourite helper, for example `yay -S gwe`.

#### Fedora
GWE avaliable in official Fedora [repos](https://src.fedoraproject.org/rpms/gwe) for F31+: `sudo dnf install gwe`

For older Fedora releases you can use [COPR package](https://copr.fedorainfracloud.org/coprs/atim/gwe/): `sudo dnf copr enable atim/gwe -y && sudo dnf install gwe`

### Build GWE from source
`./build.sh` does everything: it creates a Python virtualenv in `build/venv`, installs the Python dependencies and the
build tools (meson, ninja) listed in [requirements.txt](requirements.txt) into it, builds GWE and creates the launcher
`build/gwe`. Nothing is installed system-wide, to remove everything just delete the `build` folder.

Only a few system packages are needed, because the virtualenv can't provide a compiler, the development files of
Gtk/cairo (PyGObject and pycairo are compiled when installed) and the Gtk typelibs. On Debian/Ubuntu:

```bash
# Build time: the compiler and the development files needed to compile PyGObject and pycairo
sudo apt install build-essential pkg-config python3-dev python3-venv libcairo2-dev libgirepository1.0-dev
# Run time: the Gtk and libnotify typelibs
sudo apt install gir1.2-gtk-3.0 gir1.2-notify-0.7
# Optional: tray icon (GNOME also needs the AppIndicator extension, which is not needed to use GWE)
sudo apt install gir1.2-appindicator3-0.1
```

| Distro                | Build time                                                                                      | Run time (typelibs)                                                |
| --------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Debian/Ubuntu         | build-essential pkg-config python3-dev python3-venv libcairo2-dev libgirepository1.0-dev        | gir1.2-gtk-3.0 gir1.2-notify-0.7                                   |
| Fedora                | gcc pkgconf-pkg-config python3-devel cairo-devel gobject-introspection-devel cairo-gobject-devel | gtk3 libnotify                                                     |
| Arch Linux            | base-devel python cairo gobject-introspection                                                   | gtk3 libnotify                                                     |

The package names of the distros other than Debian/Ubuntu are not tested.

```bash
git clone https://gitlab.com/leinardi/gwe.git
cd gwe
./build.sh
build/gwe
```

Running `./build.sh` again updates the build. Set `PYTHON=python3.12 ./build.sh` to use a specific Python for the
virtualenv (tested with 3.12 and 3.13).

If you previously built GWE with `meson . build`, delete the old `build` folder once.

#### Install system-wide
Not supported by `build.sh`. It builds GWE with the prefix `build/output/install`, so the folder must stay where it is.

#### ⚠ Bumblebee and Optimus
If you want to use GWE with Bumblebee you need to start it with `optirun` and set the `--ctrl-display` parameter to `:8`:

```bash
optirun build/gwe --ctrl-display ":8"
```

## ℹ️ TODO

- [x] Show general GPU info
- [x] Show power info
- [x] Show clocks info
- [x] Show GPU temp in both app and app indicator
- [x] Show fan info
- [x] Allow to hide main app window
- [x] Add command line option to start the app hidden
- [x] Add Refresh timeout to settings
- [x] Add command line option to add desktop entry
- [x] About dialog
- [x] Distributing with PyPI
- [x] Show chart of selected fan profile
- [x] Allow to select and apply a fan profile
- [x] Add/Delete/Edit multi speed fan profiles (fan curve)
- [x] Add option to restore last applied fan profile on app startup
- [x] Find better icons for app indicator
- [x] Try to lower resource consumption (mostly caused by `nvidia-settings` invocations)
- [x] Show historical data of most important values in a separate dialog (requires GTK 3.24/GNOME 3.30)
- [x] Add overclock profiles
- [x] Add option to restore last applied overclock profile on app startup
- [ ] Disable unsupported preferences
- [x] Distributing with Flatpak
- [x] Publishing on Flathub
- [ ] Distributing with Snap
- [x] Check if NV-CONTROL is available and tell the user if is not
- [ ] Add support for multi-GPU
- [ ] Allow to select profiles from app indicator
- [ ] Add support for i18n (internationalization and localization)

<!--
## Application entry
To add a desktop entry for the application run the following command (not supported by Flatpak):
```bash
gwe --application-entry
```
If you don't want to create this custom rule you can run gwe as root
(using sudo) but we advise against this solution.
-->
## ⌨️ Command line options

  | Parameter                 | Description                               | Source | Flatpak |
  |---------------------------|-------------------------------------------|:------:|:-------:|
  |-v, --version              |Show the app version                       |    x   |    x    |
  |--debug                    |Show debug messages                        |    x   |    x    |
  |--hide-window              |Start with the main window hidden          |    x   |    x    |
  |--ctrl-display DISPLAY     |Specify the NV-CONTROL display             |    x   |    x    |
  |--gpu-index INDEX          |Index of the GPU to control (default: 0)   |    x   |    x    |
  |--header-bar               |Use the GNOME style header bar             |    x   |    x    |
  |--no-header-bar            |Use the classic title bar with a toolbar   |    x   |    x    |
  |--autostart-on             |Enable automatic start of the app on login |    x   |         |
  |--autostart-off            |Disable automatic start of the app on login|    x   |         |

## ⏱️ Refresh interval
The measurements are read every 3 seconds by default. The drop-down list next to the *Historical data* button of the main
window changes the interval (0.5, 1, 3 or 5 seconds) immediately, without restarting GWE. Any value between 0.5 and
10 seconds can be set in the settings (it is added to the list). The interval is also how often the fan profile is
applied and how often the historical data graphs get a new value.

Reading the status takes some time (all the GPUs are queried through NVML and NV-CONTROL). `gwe --debug` prints how long
it takes ("Fetching new data took ... ms"): if it takes longer than the interval, the refreshes that would overlap are
skipped, so the real rate is lower than the selected one and GWE can't get stuck. Short intervals use more CPU.

NVML is initialized once and the connection to the X server is kept open between two refreshes, they are closed and
opened again only after an error (e.g. the X server was restarted or the driver was reloaded) and when GWE quits. If you
suspect that this causes problems, start GWE with `GWE_KEEP_CONNECTIONS=0` to initialize NVML and connect to X at every
refresh, as older versions did (`gwe --debug` tells which mode is in use and how long the refreshes take).

## 🪟 Window style (GNOME, KDE and other desktops)
On GNOME (and Budgie/Pantheon) GWE uses the GNOME style header bar. On all the other desktops, e.g. KDE Plasma, it uses
the classic title bar drawn by the window manager and moves the buttons of the header bar to a toolbar below it.
The desktop is detected with `XDG_CURRENT_DESKTOP`. To force a style use the `--header-bar` or `--no-header-bar` option,
or set `GWE_HEADER_BAR` to `1` (header bar), `0` (classic) or `auto` (default). The option wins over the variable.

Only the title bars are adapted: GWE is still a Gtk3 application and uses the Gtk theme. On KDE install the Breeze Gtk
theme and `kde-gtk-config` (System Settings > Appearance > Application Style > Configure GNOME/GTK Application Style) to
get the Plasma colors, fonts and icons.

## 🖥️🖥️ Multiple GPUs
GWE controls one GPU per running instance. To manage several GPUs, start one instance for each of them and select
the GPU with the `--gpu-index` option or the `GWE_GPU_INDEX` environment variable (the option wins if both are set):

```bash
gwe --gpu-index 1
GWE_GPU_INDEX=1 gwe
```

If your system has more than one GPU, the GPU name at the top of the main window is a drop-down list: pick another
entry to control that GPU in the same window. The fan control of the GPU you leave is handed back to the driver and the
fan/overclock profiles are not applied to the new GPU until you press *Apply* (the selected profiles are kept).
Overclock offsets that were already applied to the GPU you leave stay active in the driver.

The index is the one of the NV-CONTROL extension (the same order used by `nvidia-settings`: `[gpu:N]`). The log
(`gwe --debug`) lists the index, name and UUID of every detected GPU, and an unknown index shows the list of the
available GPUs.

If you prefer one window per GPU, run one instance each (a second start for the same GPU just shows the existing
window). Every instance has its own window, fan/overclock profiles and settings: GPU 0 keeps using the existing
`~/.config/gwe/gwe.db`, the other GPUs use `~/.config/gwe/gwe-gpuN.db`. When GWE is closed it only resets the fan
control of the GPU it manages, so the other instances are not affected.

## 🖥️ Build, install and run with Flatpak
If you don't have Flatpak installed you can find step by step instructions [here](https://flatpak.org/setup/).

Make sure to have the Flathub remote added to the current user:

```bash
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### Local repository
Builds the committed state (`HEAD`, i.e. the branch that is currently checked out) of this repository. It uses the
manifest in `packaging/flatpak/`, so neither the `flatpak` submodule nor a clone with `--recurse-submodules` is needed.
The Python dependencies are downloaded from PyPI while building. Needs `flatpak`, `flatpak-builder` and
`desktop-file-utils`:
```bash
./build.sh --flatpak-local --flatpak-install
```
The GNOME runtime branch used is the one set in `packaging/flatpak/com.leinardi.gwe.json`; to try another one:
```bash
GWE_FLATPAK_RUNTIME_VERSION=50 ./build.sh --flatpak-local --flatpak-install
```
The available branches are listed by `flatpak --user remote-ls flathub --runtime | grep org.gnome.Platform`.

The NVIDIA driver extension (`org.freedesktop.Platform.GL.nvidia-<driver version>`) is not part of GWE: Flatpak picks the
one that matches the installed driver. If it is missing (all the GPU fields are empty) run `flatpak update`.

### Remote repository (the one Flathub uses, needs the submodule)
```bash
git clone --recurse-submodules -j4 https://gitlab.com/leinardi/gwe.git
./build.sh --flatpak-remote --flatpak-install
```
### Run
```bash
flatpak run com.leinardi.gwe --debug
```

## ❓ FAQ
### I see some message about CoolBits in the Overclock/Fan profile section, what's that?
Coolbits was a Windows registry hack for Nvidia graphics cards Windows drivers, that allows
tweaking features via the Nvidia driver control panel.
Something similar is available also on Linux and is the only way to enable Overclock and manual Fan control.
To know more about Coolbits and how to enable them click
[here](https://wiki.archlinux.org/index.php/NVIDIA/Tips_and_tricks#Enabling_overclocking)
(to enable both OC and Fan control you need to set it to `12`).

### The Flatpak version of GWE is not using my theme, how can I fix it?
To fix this issue install a Gtk theme from Flathub. This way, Flatpak applications will automatically pick the
installed Gtk theme and use that instead of Adwaita.

Use this command to get a list of all the available Gtk themes on Flathub:
```bash
flatpak --user remote-ls flathub | grep org.gtk.Gtk3theme
```
And then just install your preferred theme. For example, to install Yaru:
```
flatpak install flathub org.gtk.Gtk3theme.Yaru
```

### I have installed the app using Flatpak, but all the GWE fields are empty
This issue can be usually solved by closing GWE, executing `flatpak update` and starting GWE again.
This is necessary to be sure to have the latest [org.freedesktop.Platform.GL.nvidia](https://github.com/flathub/org.freedesktop.Platform.GL.nvidia).
If, after the update, all the fields are still empty, feel free to open a new issue on the project tracker.

### Why the memory overclock offsets effectively applied does not match the one set in the Nvidia Settings app?
Because Memory Transfer Rate, what Nvidia Settings reports and changes,
is different from the effective Memory Clock, what is actually being
displayed by GWE. It is also what other Windows applications like MSI Afterburner show.
The Memory Transfer Rate is simply double the Memory Clock.

### Where are the settings and profiles stored on the filesystem?
| Installation type |                     Location                     |
|-------------------|:------------------------------------------------:|
| Flatpak           |        `$HOME/.var/app/com.leinardi.gwe/`        |
| Source code       | `$XDG_CONFIG_HOME` (usually `$HOME/.config/gwe`) |

### GreenWithEnvy, why using such name?
The name comes from the slogan of the GeForce 8 series, that was "Green with envy".
Nvidia is meant to be pronounced "invidia", which means envy in Latin (and Italian). And their logo is green so, GreenWithEnvy

## 💚 How to help the project
### Help is needed for the following topics
 - Snap (see [#18](https://gitlab.com/leinardi/gwe/issues/18))
 - Getting current GTK theme text color (see [#36](https://gitlab.com/leinardi/gwe/issues/36))
 - Making Bumblebee work with Flatpak (see [#35](https://gitlab.com/leinardi/gwe/issues/35))

### Discord server
If you want to help testing or developing it would be easier to get in touch using the discord server of the project: https://discord.gg/xBybdRt
Just write a message on the general channel saying how you want to help (test, dev, etc) and quoting @leinardi. If you don't use discor but still want to help just open a new issue here.


### Can I support this project some other way?

Something simple that everyone can do is to star it on both [GitLab](https://gitlab.com/leinardi/gwe) and [GitHub](https://github.com/leinardi/gwe).
Feedback is always welcome: if you found a bug or would like to suggest a feature,
feel free to open an issue on the [issue tracker](https://gitlab.com/leinardi/gwe/issues).

## ⚠ Dropped PyPI support
Development builds were previously distributed using PyPI. This way of distributing the software is simple
but requires the user to manually install all the non Python dependencies like cairo, glib, appindicator3, etc.
The historical data used to need a new library, Dazzle (it is not needed anymore), that required Gnome 3.30 which was
available, using Python Object introspection, only starting from Ubuntu 18.10 making the latest Ubuntu LTS, 18.04,
unsupported.
A solution for all this problems is distributing the app via Flatpak, since with it all the dependencies
will be bundled and provided automatically, making possible to use Gnome 3.30 features also on distributions
using an older version of Gnome.

**No new build will be published on PyPI**.

### Uninstall pip version
If you have already installed GWE via `pip`, please make sure to uninstall it completely before moving to a newer version:

```bash
pip3 uninstall gwe
rm -rf ~/.config/gwe
```

## ℹ️ Acknowledgements
Thanks to:

 - GabMus and TingPing for the huge help with Flatpak
 - @999eagle for maintaining the [AUR package](https://aur.archlinux.org/packages/gwe/)
 - @tim74 for maintaining the [COPR package](https://copr.fedorainfracloud.org/coprs/atim/gwe/)
 - Lighty for moderating the [Discord](https://discord.gg/YjPdNff) server
 - fbcotter for the [py3nvml](https://github.com/fbcotter/py3nvml/) library
 - all the devs of the [python-xlib](https://github.com/python-xlib/python-xlib/) library
 - tiheum for the [Faenza](https://www.deviantart.com/tiheum/art/Faenza-Icons-173323228) icons set, from which I took the current GWE launcher icon
 - all the people that helped testing and reported bugs

## 📰 Media coverage
 - [OMG! Ubuntu](https://www.omgubuntu.co.uk/2019/02/easily-overclock-nvidia-gpu-on-linux-with-this-new-app) 🇬🇧
 - [GamingOnLinux](https://www.gamingonlinux.com/articles/greenwithenvy-an-impressive-tool-for-overclocking-nvidia-gpus.13521) 🇬🇧
 - [Phoronix](https://www.phoronix.com/scan.php?page=news_item&px=GreenWithEnvy-0.11-Released) 🇬🇧
 - [ComputerBase](https://www.computerbase.de/2019-02/green-envy-uebertakten-nvidia-grafikkarten-linux/) 🇩🇪
 - [lffl](https://www.lffl.org/2019/02/overclock-scheda-nvidia-linux.html) 🇮🇹
 - [osside blog](https://www.osside.net/2019/02/greenwithenvy-gwe-linux-easy-nvidia-status-overclock/) 🇮🇹
 - [Diolinux](https://www.diolinux.com.br/2019/02/greenwithenvy-uma-nova-forma-de-voce-gerenciar-gpu-nvidia.html?m=1) 🇧🇷
 - [Blog do Edivaldo](https://www.edivaldobrito.com.br/overclock-em-gpus-nvidia-no-linux/) 🇧🇷
 - [Linux Adictos](https://www.linuxadictos.com/greenwithenvy-programa-para-overclocking-en-gpus-nvidia.html) 🇪🇸


## 📝 License
```
This file is part of gwe.

Copyright (c) 2019 Roberto Leinardi

gwe is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

gwe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with gwe.  If not, see <http://www.gnu.org/licenses/>.
```