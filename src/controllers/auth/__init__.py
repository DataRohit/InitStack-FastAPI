from src.controllers.auth.base import AuthController
from src.controllers.auth.base import auth_controller
from src.controllers.auth.me import register_me_routes
from src.controllers.auth.oauth_github import register_github_oauth_routes
from src.controllers.auth.oauth_google import register_google_oauth_routes
from src.controllers.auth.reactivate import register_reactivate_routes
from src.controllers.auth.relogin import register_relogin_routes
from src.controllers.auth.reset_password import register_reset_password_routes
from src.controllers.auth.signup import register_signup_routes

__all__: list[str] = [
    "AuthController",
    "auth_controller",
    "register_activate_routes",
    "register_deactivate_routes",
    "register_forgot_password_routes",
    "register_github_oauth_routes",
    "register_google_oauth_routes",
    "register_login_routes",
    "register_logout_routes",
    "register_me_routes",
    "register_reactivate_routes",
    "register_relogin_routes",
    "register_reset_password_routes",
    "register_signup_routes",
]
