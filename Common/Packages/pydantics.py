from pydantic import (
    BaseModel, ConfigDict, Field, model_validator
)

__all__ = [ 'FrozenBaseModel', 'Field', 'model_validator' ]


class FrozenBaseModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        use_attribute_docstrings=True,
    )

