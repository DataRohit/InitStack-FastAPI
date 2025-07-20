# Standard Library Imports
from typing import Any

# Third-Party Imports
from pydantic import BaseModel, Field


# Health Response Model
class HealthResponse(BaseModel):
    """
    Health Response Model

    This Model Defines the Structure of the Health Check Response.

    Attributes:
        status: Current status of the API.
        app: Name of the application.
        version: Current version of the API.
        environment: Current environment.
    """

    # Model Fields
    status: str = Field(examples=["healthy"])
    app: str = Field(examples=["InitStack"])
    version: str = Field(examples=["1.0.0"])
    environment: str = Field(examples=["development", "production"])

    # Class Methods
    @classmethod
    def get_health_response(cls) -> dict[str, Any]:
        """
        Get Health Response

        This Method Returns the Health Status of the API.

        Returns:
            dict[str, Any]: Health status information.
        """

        # Return Health Response
        return {
            "status": "healthy",
            "app": "InitStack",
            "version": "1.0.0",
            "environment": "development",
        }


# Exports
__all__: list[str] = ["HealthResponse"]
