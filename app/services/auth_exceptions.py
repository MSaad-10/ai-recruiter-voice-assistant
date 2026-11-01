class AuthError(Exception):
    pass


class InvalidOtpError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class EmailNotVerifiedError(AuthError):
    pass


class InactiveAccountError(AuthError):
    pass