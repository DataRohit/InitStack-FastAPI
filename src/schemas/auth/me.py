from src.schemas.auth.signup import SignUpResponse


class MeResponse(SignUpResponse):
    """Me Response Schema.

    Inherits:
        SignUpResponse
    """


__all__: list[str] = ["MeResponse"]
