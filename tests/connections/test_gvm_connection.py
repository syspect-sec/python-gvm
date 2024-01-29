# SPDX-FileCopyrightText: 2020-2024 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import unittest
from unittest.mock import patch

from gvm.connections import DEFAULT_TIMEOUT, GvmConnection, XmlReader
from gvm.errors import GvmError


class XmlReaderTestCase(unittest.TestCase):
    def test_is_end_xml_false(self):
        reader = XmlReader()
        reader.start_xml()

        false = reader.is_end_xml()
        self.assertFalse(false)


class GvmConnectionTestCase(unittest.TestCase):
    # pylint: disable=protected-access
    def test_init_no_args(self):
        connection = GvmConnection()
        self.check_for_default_values(connection)

    def test_init_with_none(self):
        connection = GvmConnection(timeout=None)
        self.check_for_default_values(connection)

    def check_for_default_values(self, gvm_connection: GvmConnection):
        self.assertIsNone(gvm_connection._socket)
        self.assertEqual(gvm_connection._timeout, DEFAULT_TIMEOUT)

    def test_connect_not_implemented(self):
        connection = GvmConnection()
        with self.assertRaises(NotImplementedError):
            connection.connect()

    @patch("gvm.connections.GvmConnection._read")
    def test_read_no_data(self, _read_mock):
        _read_mock.return_value = None
        connection = GvmConnection()
        with self.assertRaises(GvmError, msg="Remote closed the connection"):
            connection.read()

    @patch("gvm.connections.GvmConnection._read")
    def test_read_trigger_timeout(self, _read_mock):
        # mocking the response into two parts, so we run into the timeout
        # check in the loop
        _read_mock.side_effect = [b"<foo>xyz<bar></bar>", b"</foo>"]
        connection = GvmConnection(timeout=0)
        with self.assertRaises(
            GvmError, msg="Timeout while reading the response"
        ):
            connection.read()
