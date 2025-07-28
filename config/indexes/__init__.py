# Local Imports
from config.indexes.profiles import create_profiles_indexes
from config.indexes.users import create_users_indexes

# Exports
__all__: list[str] = ["create_profiles_indexes", "create_users_indexes"]
