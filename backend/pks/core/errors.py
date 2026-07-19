"""Errors raised by the Core Knowledge Engine."""


class KnowledgeError(Exception):
    """Base class for engine errors."""


class NotFoundError(KnowledgeError):
    """The referenced object does not exist."""


class ValidationError(KnowledgeError):
    """The operation's arguments are invalid."""
