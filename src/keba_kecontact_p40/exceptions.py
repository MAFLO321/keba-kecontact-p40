"""Exceptions for the KEBA P40 client."""


class KebaP40Error(Exception):
    """Base error for all KEBA P40 client failures."""


class KebaP40ConnectionError(KebaP40Error):
    """Raised when the wallbox cannot be reached."""


class KebaP40AuthError(KebaP40Error):
    """Raised when authentication with the wallbox fails."""
