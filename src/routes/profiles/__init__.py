# Local Imports
from src.routes.profiles.base import router
from src.routes.profiles.create import create_profile
from src.routes.profiles.read import read_profile
from src.routes.profiles.update import update_profile
from src.routes.profiles.delete import delete_profile
from src.routes.profiles.avatar import update_avatar

# Exports
__all__: list[str] = ["router"]
