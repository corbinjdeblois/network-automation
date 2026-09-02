"""Validated data models for read-only device inventory operations."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Device(BaseModel):
	"""Normalized metadata collected from a network device.

	This model intentionally contains inventory and software metadata only.
	Credentials and configuration payloads must not be represented here.
	"""

	model_config = ConfigDict(
		extra="forbid",
		frozen=True,
		str_strip_whitespace=True,
	)

	hostname: str = Field(min_length=1, max_length=253)
	vendor: str = Field(min_length=1, max_length=100)
	model: str = Field(min_length=1, max_length=100)
	serial_number: str = Field(min_length=1, max_length=100)
	software_version: str = Field(min_length=1, max_length=100)

	@field_validator(
		"hostname",
		"vendor",
		"model",
		"serial_number",
		"software_version",
	)
	@classmethod
	def reject_control_characters(cls, value: str) -> str:
		"""Reject values that could corrupt logs or serialized output."""
		if any(character < " " for character in value):
			raise ValueError("value must not contain control characters")
		return value


__all__ = ["Device"]
