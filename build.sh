#!/bin/bash

cd "$(dirname "$(readlink -f "$0")")" || exit 1

POSITIONAL=()
while [[ $# -gt 0 ]]
do
	key="$1"

	case ${key} in
		-fl|--flatpak-local)
			FLATPAK_LOCAL=1
			shift # past argument
			;;
		-fr|--flatpak-remote)
			FLATPAK_REMOTE=1
			shift # past argument
			;;
		-fi|--flatpak-install)
			FLATPAK_INSTALL=1
			shift # past argument
			;;
		-fb|--flatpak-bundle)
			FLATPAK_BUNDLE=1
			shift # past argument
			;;
		*)    # unknown option
			POSITIONAL+=("$1") # save it in an array for later
			shift # past argument
			;;
	esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

APP_ID="com.leinardi.gwe"
BUILD_DIR="build"
OUTPUT_DIR="${BUILD_DIR}/output"
MESON_BUILD_DIR="${BUILD_DIR}/meson"
FLATPAK_BUILD_DIR="${BUILD_DIR}/flatpak/build"
FLATPAK_REPO_DIR="${BUILD_DIR}/flatpak/repo"
FLATPAK_INSTALL_PARAMETERS="--user --install"
FLATPAK_REMOTE_MANIFEST="flatpak/${APP_ID}.json"
# The manifest used for the local builds is part of this repository (it does not need the flatpak submodule)
FLATPAK_LOCAL_SOURCE_MANIFEST="packaging/flatpak/${APP_ID}.json"
FLATPAK_LOCAL_MANIFEST="build/flatpak/${APP_ID}.json"
FLATPAK_OUTPUT_FILE="${OUTPUT_DIR}/${APP_ID}.flatpak"
INSTALL_DIR="${OUTPUT_DIR}/install"

function build_flatpak {
	mkdir -p ${FLATPAK_REPO_DIR} && \
	mkdir -p ${FLATPAK_BUILD_DIR} && \

	time flatpak-builder --force-clean $2 --install-deps-from=flathub --repo=${FLATPAK_REPO_DIR} ${FLATPAK_BUILD_DIR} $1 && \
	desktop-file-validate build/flatpak/build/files/share/applications/com.leinardi.gwe.desktop || exit $?
}

function build_flatpak_bundle {
	mkdir -p ${OUTPUT_DIR} && \
	time flatpak build-bundle ${FLATPAK_REPO_DIR} ${FLATPAK_OUTPUT_FILE} ${APP_ID} || exit $?
}

function prepare_release_files {
	appstream-util validate-relax data/com.leinardi.gwe.appdata.xml || exit $?
	appstream-util appdata-to-news data/com.leinardi.gwe.appdata.xml | sed '/^~*$/s/~/=/g' > CHANGELOG.md
}

# Builds GWE into build/output/install using a virtualenv (build/venv) that contains all the Python dependencies and
# the build tools (see requirements.txt), and creates the launcher build/gwe.
# Only the system packages listed in the "Build GWE from source" section of the README are needed.
function build_local {
	local venv="${BUILD_DIR}/venv"
	local python="${PYTHON:-python3}"
	local apt_build_packages="build-essential pkg-config python3-dev python3-venv libcairo2-dev libgirepository1.0-dev"
	local apt_runtime_packages="gir1.2-gtk-3.0 gir1.2-notify-0.7"

	if ! command -v gcc > /dev/null || ! command -v pkg-config > /dev/null \
		|| ! pkg-config --exists cairo gobject-introspection-1.0 \
		|| ! "${python}" -c 'import venv, ensurepip' 2> /dev/null; then
		echo "Some of the packages needed to build GWE are missing. On Debian/Ubuntu install them with:"
		echo "    sudo apt install ${apt_build_packages}"
		return 1
	fi

	(
		set -e
		[[ -x ${venv}/bin/python ]] || "${python}" -m venv "${venv}"
		"${venv}/bin/python" -m pip install --upgrade pip
		"${venv}/bin/python" -m pip install -r requirements.txt

		# Fail now, not when the app is started
		"${venv}/bin/python" - << 'EOF' || { echo "Missing typelibs. On Debian/Ubuntu install them with:"; \
			echo "    sudo apt install ${apt_runtime_packages}"; exit 1; }
import gi
for namespace, version in (('Gtk', '3.0'), ('Gdk', '3.0'), ('Notify', '0.7')):
    gi.require_version(namespace, version)
EOF

		# meson and ninja come from the venv: this way the generated gwe script uses the Python of the venv too
		export PATH="${PWD}/${venv}/bin:${PATH}"
		[[ -d ${MESON_BUILD_DIR} ]] && rm -rfv "${MESON_BUILD_DIR}"
		mkdir -pv "${MESON_BUILD_DIR}" "${INSTALL_DIR}"
		meson setup . "${MESON_BUILD_DIR}" --prefix="${PWD}/${INSTALL_DIR}"
		ninja -v -C "${MESON_BUILD_DIR}"
		if command -v desktop-file-validate > /dev/null; then
			desktop-file-validate "${MESON_BUILD_DIR}/data/com.leinardi.gwe.desktop"
		fi
		ninja -v -C "${MESON_BUILD_DIR}" install

		cat > "${BUILD_DIR}/gwe" << 'EOF'
#!/bin/bash
dir="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec "${dir}/venv/bin/python" "${dir}/output/install/bin/gwe" "$@"
EOF
		chmod +x "${BUILD_DIR}/gwe"
	) || return $?

	echo
	echo "Done. Start GWE with: ${BUILD_DIR}/gwe"
}

if [[ ${#POSITIONAL[@]} -ne 0 ]]; then
	echo "Unknown option ${POSITIONAL}"
	exit 1
fi

# Release step (it also overwrites CHANGELOG.md): not needed to just build and install GWE locally
if [[ ${FLATPAK_REMOTE} -eq 1 || ${FLATPAK_BUNDLE} -eq 1 ]]; then
	prepare_release_files
fi
[[ -d ${OUTPUT_DIR} ]] && rm -rfv ${OUTPUT_DIR}
# build/ is skipped: it contains the venv
find . \( -path ./build -o -path ./.git \) -prune -o \( -name __pycache__ -o -name '*.py[co]' \) -exec rm -rf {} +

if [[ ${FLATPAK_REMOTE} -eq 1 ]]; then
	if [[ ${FLATPAK_INSTALL} -eq 1 ]]; then
		build_flatpak "${FLATPAK_REMOTE_MANIFEST}" "${FLATPAK_INSTALL_PARAMETERS}"
	else
		build_flatpak ${FLATPAK_REMOTE_MANIFEST}
	fi
	if [[ ${FLATPAK_BUNDLE} -eq 1 ]]; then
		build_flatpak_bundle
	fi
elif [[ ${FLATPAK_LOCAL} -eq 1 ]]; then
	scripts/make_local_manifest.py ${FLATPAK_LOCAL_SOURCE_MANIFEST} ${FLATPAK_LOCAL_MANIFEST}
	if [[ ${FLATPAK_INSTALL} -eq 1 ]]; then
		build_flatpak "${FLATPAK_LOCAL_MANIFEST}" "${FLATPAK_INSTALL_PARAMETERS}"
	else
		build_flatpak ${FLATPAK_LOCAL_MANIFEST}
	fi
	if [[ ${FLATPAK_BUNDLE} -eq 1 ]]; then
		build_flatpak_bundle
	fi
elif [[ ${FLATPAK_BUNDLE} -eq 1 ]]; then
	build_flatpak_bundle
else
	build_local || exit $?
fi
