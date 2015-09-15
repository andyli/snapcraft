# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2015 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from unittest.mock import (
    call,
    mock_open,
    patch,
)

from snapcraft import (
    common,
    meta,
    tests
)


class ComposeTestCase(tests.TestCase):

    def setUp(self):
        super().setUp()
        patcher = patch('snapcraft.meta._wrap_exe')
        mock_wrap_exe = patcher.start()
        mock_wrap_exe.return_value = 'binary.wrapped'
        self.addCleanup(patcher.stop)

        self.config_data = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'icon': 'my-icon.png',
        }

    def test_plain_no_binaries_or_services(self):

        y = meta._compose_package_yaml(self.config_data, ['armhf', 'amd64'])

        expected = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'icon': 'my-icon.png',
            'architectures': ['armhf', 'amd64'],
        }

        self.assertEqual(y, expected)

    def test_plain_no_binaries_or_services_or_arches(self):

        y = meta._compose_package_yaml(self.config_data, None)

        expected = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'icon': 'my-icon.png',
        }

        self.assertEqual(y, expected)

    def test_with_binaries(self):
        self.config_data['binaries'] = [
            {
                'name': 'binary1',
                'exec': 'binary1.sh go',
            },
            {
                'name': 'binary2',
            },
        ]

        y = meta._compose_package_yaml(self.config_data, ['armhf', 'amd64'])

        expected = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'icon': 'my-icon.png',
            'architectures': ['armhf', 'amd64'],
            'binaries': [
                {
                    'name': 'binary1',
                    'exec': 'binary.wrapped go',
                },
                {
                    'name': 'binary2',
                    'exec': 'binary.wrapped',
                },
            ],
        }

        self.assertEqual(y, expected)

    def test_with_services(self):
        self.config_data['services'] = [
            {
                'name': 'service1',
                'start': 'binary1',
            },
            {
                'name': 'service2',
                'start': 'binary2 --start',
                'stop': 'binary2 --stop',
            },
            {
                'name': 'service3',
            },
        ]

        y = meta._compose_package_yaml(self.config_data, ['armhf', 'amd64'])

        expected = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'icon': 'my-icon.png',
            'architectures': ['armhf', 'amd64'],
            'services': [
                {
                    'name': 'service1',
                    'start': 'binary.wrapped',
                },
                {
                    'name': 'service2',
                    'start': 'binary.wrapped --start',
                    'stop': 'binary.wrapped --stop',
                },
                {
                    'name': 'service3',
                }
            ],
        }

        self.assertEqual(y, expected)

    def test_plain_no_binaries_or_services_with_optionals(self):
        self.config_data['frameworks'] = ['mir', ]

        y = meta._compose_package_yaml(self.config_data, ['armhf', 'amd64'])

        expected = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'icon': 'my-icon.png',
            'architectures': ['armhf', 'amd64'],
            'frameworks': ['mir', ],
        }

        self.assertEqual(y, expected)

    def test_compose_readme(self):
        self.config_data['summary'] = 'one line summary'
        self.config_data['description'] = 'the description\nwhich can be longer'

        readme_text = '''one line summary
the description
which can be longer
'''

        self.assertEqual(meta._compose_readme(self.config_data), readme_text)


class Create(tests.TestCase):

    def setUp(self):
        super().setUp()
        patcher_makedirs = patch('os.makedirs')
        self.mock_makedirs = patcher_makedirs.start()
        self.addCleanup(patcher_makedirs.stop)

        patcher_copyfile = patch('shutil.copyfile')
        self.mock_copyfile = patcher_copyfile.start()
        self.addCleanup(patcher_copyfile.stop)

        self.config_data = {
            'name': 'my-package',
            'version': '1.0',
            'vendor': 'Sergio Schvezov <sergio.schvezov@canonical.com>',
            'description': 'my description',
            'summary': 'my summary',
            'icon': 'my-icon.png',
        }

    def test_create_meta(self):
        mock_the_open = mock_open()

        with patch('snapcraft.meta.open', mock_the_open, create=True):
            meta.create(self.config_data, ['amd64'])

        meta_dir = os.path.join(os.path.abspath(os.curdir), 'snap', 'meta')

        self.mock_makedirs.assert_called_once_with(meta_dir, exist_ok=True)

        mock_the_open.assert_has_calls([
            call(os.path.join(meta_dir, 'package.yaml'), 'w'),
            call().__enter__(),
            call().write('architectures'),
            call().write(':'),
            call().write('\n'),
            call().write('-'),
            call().write(' '),
            call().write('amd64'),
            call().write('\n'),
            call().write('icon'),
            call().write(':'),
            call().write(' '),
            call().write('meta/my-icon.png'),
            call().write('\n'),
            call().write('name'),
            call().write(':'),
            call().write(' '),
            call().write('my-package'),
            call().write('\n'),
            call().write('vendor'),
            call().write(':'),
            call().write(' '),
            call().write('Sergio'),
            call().write(' '),
            call().write('Schvezov'),
            call().write(' '),
            call().write('<sergio.schvezov@canonical.com>'),
            call().write('\n'),
            call().write('version'),
            call().write(':'),
            call().write(" '"),
            call().write('1.0'),
            call().write("'"),
            call().write('\n'),
            call().flush(),
            call().flush(),
            call().__exit__(None, None, None),
            call(os.path.join(meta_dir, 'readme.md'), 'w'),
            call().__enter__(),
            call().write('my summary\nmy description\n'),
            call().__exit__(None, None, None),
        ]
        )


# TODO this needs more tests.
class WrapExeTestCase(tests.TestCase):

    def test_wrap_exe_must_write_wrapper(self):
        snapdir = common.get_snapdir()
        os.mkdir(snapdir)
        relative_exe_path = 'test_relexepath'
        relative_wrapper_path = meta._wrap_exe(relative_exe_path)
        wrapper_path = os.path.join(snapdir, relative_wrapper_path)

        expected = ('#!/bin/sh\n'
                    '\n'
                    'exec "$SNAP_APP_PATH/test_relexepath" $*\n')
        with open(wrapper_path) as wrapper_file:
            wrapper_contents = wrapper_file.read()

        self.assertEqual(expected, wrapper_contents)