"""Ownership confirmation. Checks must not run unless this passes."""

from securecheck.constants import REFUSAL_MESSAGE


class AuthorisationRequired(Exception):
    """Raised when a check is asked to run without the confirmation flag."""


def require_authorised(authorised: bool) -> None:
    """Stop before any network call unless confirmation was given.

    ``authorised`` must be the boolean ``True``. A domain string, a file
    path, or any other truthy value is not confirmation.
    """

    if authorised is not True:
        raise AuthorisationRequired(REFUSAL_MESSAGE)
