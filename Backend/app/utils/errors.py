"""Domain errors. Subclass ValueError so older `except ValueError` paths still work."""


class NotFoundError(ValueError):
    """The requested resource does not exist (HTTP 404)."""


class ConflictError(ValueError):
    """The request conflicts with current state, e.g. an invalid transition (HTTP 409)."""
