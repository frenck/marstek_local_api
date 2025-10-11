"""Exceptions for Marstek integration."""


class MarstekException(Exception):
    """Base exception for Marstek integration."""


class MarstekConnectionException(MarstekException):
    """Exception for connection issues."""


class MarstekTimeoutException(MarstekException):
    """Exception for timeout issues."""


class MarstekDataException(MarstekException):
    """Exception for data parsing issues."""