# Copyright 1999-2023 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8
DISTUTILS_USE_PEP517=setuptools
PYTHON_COMPAT=( python3_{10..12} )

inherit distutils-r1

DESCRIPTION="This is a script for AI-generated image."
HOMEPAGE="https://github.com/yui-tan/pyPromptChecker"
SRC_URI="https://github.com/yui-tan/pyPromptChecker/archive/refs/tags/v${PV}.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="amd64"
IUSE=""

RDEPEND="
         dev-python/pypng
         dev-python/pillow
         dev-python/PyQt6
         "
DEPEND="${RDEPEND}"
BDEPEND=""

python_install() {
	distutils-r1_python_install
}
