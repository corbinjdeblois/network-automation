"""Read-only connectivity client for supported network devices."""

from __future__ import annotations

import os
import re
from typing import Any

from netmiko import ConnectHandler
from netmiko.exceptions import (
	NetmikoAuthenticationException,
	NetmikoBaseException,
	NetmikoTimeoutException,
)

from app.connectivity.models import Device


class DeviceClientError(Exception):
	"""Base exception for device connectivity and collection failures."""


class DeviceAuthenticationError(DeviceClientError):
	"""Raised when a device rejects the supplied credentials."""


class DeviceConnectionError(DeviceClientError):
	"""Raised when an SSH session cannot be established or used."""


class DeviceDataError(DeviceClientError):
	"""Raised when device metadata cannot be parsed reliably."""


class DeviceClient:
	"""Collect normalized metadata from a Cisco IOS device over SSH.

	Credentials are read from ``NETWORK_DEVICE_USERNAME`` and
	``NETWORK_DEVICE_PASSWORD``. The client only executes ``show version``;
	no configuration or write operations are exposed.
	"""

	_DEVICE_TYPE = "cisco_ios"
	_SHOW_VERSION_COMMAND = "show version"

	def __init__(
		self,
		hostname: str,
		*,
		port: int = 22,
		username: str | None = None,
		password: str | None = None,
		conn_timeout: int = 10,
	) -> None:
		"""Initialize a client for one Cisco IOS device.

		Args:
			hostname: DNS name or IP address of the device.
			port: SSH port used by the device.
			username: Optional override for the environment credential.
			password: Optional override for the environment credential.
			conn_timeout: SSH connection timeout in seconds.
		"""
		if not hostname or not hostname.strip():
			raise ValueError("hostname must not be empty")
		if not 1 <= port <= 65535:
			raise ValueError("port must be between 1 and 65535")
		if conn_timeout <= 0:
			raise ValueError("conn_timeout must be greater than zero")

		self.hostname = hostname.strip()
		self.port = port
		self.username = username or os.getenv("NETWORK_DEVICE_USERNAME")
		self.password = password or os.getenv("NETWORK_DEVICE_PASSWORD")
		self.conn_timeout = conn_timeout

	@staticmethod
	def _required_credential(value: str | None, name: str) -> str:
		if not value or not value.strip():
			raise DeviceAuthenticationError(
				f"Missing required credential: {name}"
			)
		return value

	def _connection_parameters(self) -> dict[str, Any]:
		"""Build the restricted Netmiko connection parameters."""
		return {
			"device_type": self._DEVICE_TYPE,
			"host": self.hostname,
			"port": self.port,
			"username": self._required_credential(
				self.username, "NETWORK_DEVICE_USERNAME"
			),
			"password": self._required_credential(
				self.password, "NETWORK_DEVICE_PASSWORD"
			),
			"conn_timeout": self.conn_timeout,
		}

	def get_device(self) -> Device:
		"""Connect, collect metadata, disconnect, and return a validated device.

		Raises:
			DeviceAuthenticationError: If credentials are missing or rejected.
			DeviceConnectionError: If the SSH session fails.
			DeviceDataError: If required metadata is absent from the output.
		"""
		connection = None
		try:
			connection = ConnectHandler(**self._connection_parameters())
			output = connection.send_command(self._SHOW_VERSION_COMMAND)
			return self._parse_device(output)
		except NetmikoAuthenticationException as error:
			raise DeviceAuthenticationError(
				f"Authentication failed for {self.hostname}"
			) from error
		except (NetmikoTimeoutException, NetmikoBaseException) as error:
			raise DeviceConnectionError(
				f"Unable to connect to {self.hostname} over SSH"
			) from error
		finally:
			if connection is not None:
				connection.disconnect()

	@classmethod
	def _parse_device(cls, output: str) -> Device:
		"""Parse the Cisco ``show version`` response into a validated model."""
		patterns = {
			"hostname": (
				r"^([^\s]+)\s+uptime is",
				r"^([^\s()]+)[>#]\s*$",
			),
			"model": (
				r"^cisco\s+(\S+)\s+\([^)]*\)\s+processor",
				r"^cisco\s+(\S+)\s+processor",
			),
			"serial_number": (r"Processor board ID\s+(\S+)",),
			"software_version": (r"Version\s+([^,\s]+)",),
		}
		values: dict[str, str] = {}

		for field_name, field_patterns in patterns.items():
			for pattern in field_patterns:
				match = re.search(pattern, output, re.MULTILINE | re.IGNORECASE)
				if match:
					values[field_name] = match.group(1).strip()
					break

		values["vendor"] = "Cisco"
		missing_fields = {
			field_name
			for field_name in (
				"hostname",
				"model",
				"serial_number",
				"software_version",
			)
			if field_name not in values
		}
		if missing_fields:
			raise DeviceDataError(
				"Unable to parse required device fields: "
				+ ", ".join(sorted(missing_fields))
			)

		try:
			return Device(**values)
		except ValueError as error:
			raise DeviceDataError("Parsed device metadata failed validation") from error


__all__ = [
	"DeviceAuthenticationError",
	"DeviceClient",
	"DeviceClientError",
	"DeviceConnectionError",
	"DeviceDataError",
]
