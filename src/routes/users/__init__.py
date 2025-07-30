# Local Imports
from src.routes.users.base import router
from src.routes.users.register import register_user
from src.routes.users.activate import activate_user
from src.routes.users.login import login_user
from src.routes.users.me import get_current_user
from src.routes.users.deactivate import deactivate_user
from src.routes.users.deactivate_confirm import deactivate_user_confirm
from src.routes.users.delete import delete_user
from src.routes.users.delete_confirm import delete_user_confirm
from src.routes.users.reset_password import reset_password
from src.routes.users.reset_password_confirm import reset_password_confirm
from src.routes.users.check_username import check_username
from src.routes.users.update_username import update_username
from src.routes.users.update_username_confirm import update_username_confirm
from src.routes.users.update_email import update_email
from src.routes.users.update_email_confirm import update_email_confirm


# Exports
__all__: list[str] = ["router"]
