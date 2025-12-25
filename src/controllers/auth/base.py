# ruff: noqa: TC003

import logging

from argon2 import PasswordHasher
from fastapi import APIRouter

from config.logger import get_logger
from src.controllers.auth.signup import register_signup_routes


class AuthController:
    """Authentication Controller With All Auth Routes.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for auth operations.
        _password_hasher (PasswordHasher): Password hasher.
        router (APIRouter): FastAPI router for auth endpoints.

    Properties:
        None

    Methods:
        _setup_routes: Setup FastAPI routes for auth endpoints.
    """

    def __init__(self) -> None:
        """Initialize Auth Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.auth")
        self._password_hasher: PasswordHasher = PasswordHasher()
        self.router: APIRouter = APIRouter(prefix="/auth", tags=["Auth"])
        self._setup_routes()

        self._logger.info(msg="Auth controller initialized")

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For Auth Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        register_signup_routes(
            router=self.router,
            logger=self._logger,
            password_hasher=self._password_hasher,
        )


auth_controller: AuthController = AuthController()


__all__: list[str] = ["AuthController", "auth_controller"]
