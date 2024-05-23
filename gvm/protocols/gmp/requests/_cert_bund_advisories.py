# SPDX-FileCopyrightText: 2024 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional

from gvm.errors import RequiredArgument
from gvm.protocols.core import Request
from gvm.utils import to_bool
from gvm.xml import XmlCommand

from ._entity_id import EntityID


class CertBundAdvisories:

    @staticmethod
    def get_cert_bund_advisories(
        *,
        filter_string: Optional[str] = None,
        filter_id: Optional[EntityID] = None,
        name: Optional[str] = None,
        details: Optional[bool] = None,
    ) -> Request:
        """Request a list of CERT-BUND Advisories

        Args:
            filter_string: Filter term to use for the query
            filter_id: UUID of an existing filter to use for the query
            name: Name or identifier of the requested information
            details: Whether to include information about references to this
                information
        """
        cmd = XmlCommand("get_info")

        cmd.set_attribute("type", "CERT_BUND_ADV")

        cmd.add_filter(filter_string, filter_id)

        if name:
            cmd.set_attribute("name", name)

        if details is not None:
            cmd.set_attribute("details", to_bool(details))

        return cmd

    @classmethod
    def get_cert_bund_advisory(cls, cert_id: EntityID) -> Request:
        """Request a single CERT-BUND Advisory

        Args:
            cert_id: ID of an existing CERT-BUND Advisory
        """
        if not cert_id:
            raise RequiredArgument(
                function=cls.get_cert_bund_advisory.__name__, argument="cert_id"
            )

        cmd = XmlCommand("get_info")
        cmd.set_attribute("info_id", str(cert_id))
        cmd.set_attribute("type", "CERT_BUND_ADV")

        # for single entity always request all details
        cmd.set_attribute("details", "1")

        return cmd
