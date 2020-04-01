# -*- coding: utf-8 -*-
# Copyright (C) 2020 Greenbone Networks GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import re
import subprocess
import sys

from pathlib import Path
from typing import Union

import tomlkit

from packaging.version import Version, InvalidVersion


from gvm import get_version


def strip_version(version: str) -> str:
    """
    Strips a leading 'v' from a version string

    E.g. v1.2.3 will be converted to 1.2.3
    """
    if version and version[0] == 'v':
        return version[1:]

    return version


def safe_version(version: str) -> str:
    """
    Returns the version as a string in `PEP440`_ compliant
    format.

    .. _PEP440:
       https://www.python.org/dev/peps/pep-0440
    """
    try:
        return str(Version(version))
    except InvalidVersion:
        version = version.replace(' ', '.')
        return re.sub('[^A-Za-z0-9.]+', '-', version)


def get_version_from_pyproject_toml(pyproject_toml_path: Path = None) -> str:
    """
    Return the version information from the [tool.poetry] section of the
    pyproject.toml file. The version may be in non standardized form.
    """
    if not pyproject_toml_path:
        path = Path(__file__)
        pyproject_toml_path = path.parent.parent / 'pyproject.toml'

    if not pyproject_toml_path.exists():
        raise RuntimeError('pyproject.toml file not found.')

    pyproject_toml = tomlkit.parse(pyproject_toml_path.read_text())
    if (
        'tool' in pyproject_toml
        and 'poetry' in pyproject_toml['tool']
        and 'version' in pyproject_toml['tool']['poetry']
    ):
        return pyproject_toml['tool']['poetry']['version']

    raise RuntimeError('Version information not found in pyproject.toml file.')


def get_version_string(version: tuple) -> str:
    """Create a version string from a version tuple

    Arguments:
        version: version as tuple e.g. (1, 2, 0, dev, 5)

    Returns:
        The version tuple converted into a string representation
    """
    if len(version) > 4:
        ver = ".".join(str(x) for x in version[:4])
        ver += str(version[4])

        if len(version) > 5:
            # support (1, 2, 3, 'beta', 2, 'dev', 1)
            ver += ".{0}{1}".format(str(version[5]), str(version[6]))

        return ver
    else:
        return ".".join(str(x) for x in version)


def print_version(pyproject_toml_path: Path = None) -> None:
    pyproject_version = get_version_from_pyproject_toml(
        pyproject_toml_path=pyproject_toml_path
    )

    print(pyproject_version)


def check_version_equal(new_version: str, old_version: str) -> bool:
    """
    Checks if new_version and old_version equal
    """
    return safe_version(old_version) == safe_version(new_version)


def is_version_pep440_compliant(version: str) -> bool:
    """
    Checks if the provided version is a PEP 440 compliant version string
    """
    return version == safe_version(version)


def update_pyproject_version(
    new_version: str, cwd: Union[Path, str] = None,
) -> None:
    """
    Update the version in the pyproject.toml file
    """
    version = safe_version(new_version)

    subprocess.check_call(
        ['poetry', 'version', version],
        stdout=subprocess.DEVNULL,
        timeout=120,  # wait 2 min and don't wait forever
        cwd=str(cwd),
    )


def update_version_file(new_version: str, version_file_path: Path) -> None:
    """
    Update the version file with the new version
    """
    version = safe_version(new_version)

    text = """# pylint: disable=invalid-name

# THIS IS AN AUTOGENERATED FILE. DO NOT TOUCH!

__version__ = "{}"\n""".format(
        version
    )
    version_file_path.write_text(text)


def _update_python_gvm_version(
    new_version: str, pyproject_toml_path: Path, *, force: bool = False
):
    if not pyproject_toml_path.exists():
        sys.exit(
            'Could not find pyproject.toml file in the current working dir.'
        )

    cwd_path = Path.cwd()
    python_gvm_version = get_version()
    pyproject_version = get_version_from_pyproject_toml(
        pyproject_toml_path=pyproject_toml_path
    )
    version_file_path = cwd_path / 'gvm' / '__version__.py'

    if not pyproject_toml_path.exists():
        sys.exit(
            'Could not find __version__.py file at {}.'.format(
                version_file_path
            )
        )

    if not force and not check_version_equal(new_version, python_gvm_version):
        print('Version is already up-to-date.')
        sys.exit(0)

    try:
        update_pyproject_version(new_version=new_version, cwd=cwd_path)
    except subprocess.SubprocessError as e:
        sys.exit(e)

    update_version_file(
        new_version=new_version, version_file_path=version_file_path,
    )

    print(
        'Updated version from {} to {}'.format(
            pyproject_version, safe_version(new_version)
        )
    )


def _verify_version(version: str, pyproject_toml_path: Path) -> None:
    python_gvm_version = get_version()
    pyproject_version = get_version_from_pyproject_toml(
        pyproject_toml_path=pyproject_toml_path
    )
    if not is_version_pep440_compliant(python_gvm_version):
        sys.exit("The version in gvm/__version__.py is not PEP 440 compliant.")

    if pyproject_version != python_gvm_version:
        sys.exit(
            "The version set in the pyproject.toml file \"{}\" doesn't "
            "match the python-gvm version \"{}\"".format(
                pyproject_version, python_gvm_version
            )
        )

    if version != 'current':
        provided_version = strip_version(version)
        if provided_version != python_gvm_version:
            sys.exit(
                "Provided version \"{}\" does not match the python-gvm "
                "version \"{}\"".format(provided_version, python_gvm_version)
            )

    print('OK')


def main():
    parser = argparse.ArgumentParser(
        description='Version handling utilities for python-gvm.', prog='version'
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        help='additional help',
        dest='command',
    )

    verify_parser = subparsers.add_parser('verify')
    verify_parser.add_argument('version', help='version string to compare')

    subparsers.add_parser('show')

    update_parser = subparsers.add_parser('update')
    update_parser.add_argument('version', help='version string to use')
    update_parser.add_argument(
        '--force',
        help="don't check if version is already set",
        action="store_true",
    )

    args = parser.parse_args()

    if not getattr(args, 'command', None):
        parser.print_usage()
        sys.exit(0)

    pyproject_toml_path = Path.cwd() / 'pyproject.toml'

    if args.command == 'update':
        _update_python_gvm_version(
            args.version,
            pyproject_toml_path=pyproject_toml_path,
            force=args.force,
        )
    elif args.command == 'show':
        print_version(pyproject_toml_path=pyproject_toml_path)
    elif args.command == 'verify':
        _verify_version(args.version, pyproject_toml_path=pyproject_toml_path)


if __name__ == '__main__':
    main()
