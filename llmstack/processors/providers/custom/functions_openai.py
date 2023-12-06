from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class Type(Enum):
    Str = "string", "str"
    Int = "integer", "int"
    Bool = "boolean", "bool"

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __repr__(self):
        return '<%s.%s: %s>' % (
            self.__class__.__name__,
            self._name_,
            ', '.join([repr(v) for v in self._all_values]),
        )


class Property(BaseModel):
    variable_name: str
    description: str
    variable_type: Type
    enum_: Optional[List] = None

    class Config:
        use_enum_values = True


def create_openai_function_schema(properties: List[Property], function_name: str, function_description: str):
    temp_props = dict()
    for property in properties:
        temp_props[property.variable_name] = {"type": property.variable_type, "description": property.description}
        enum_ = property.enum_
        if enum_:
            temp_props[property.variable_name]["enum"] = enum_
    required = [property.variable_name for property in properties]
    return [
        {
            "name": function_name,
            "description": function_description,
            "parameters": {
                "type": "object",
                "properties": temp_props,
                "required": required,
            },
        }
    ]
