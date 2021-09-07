from dataclasses import dataclass
from carica.interface import SerializableType, ISerializable, primativeTypes, PrimativeType, objectIsShallowSerializable, objectIsDeepSerializable
from typing import Any, Dict, cast


@dataclass
class SerializableDataClass(ISerializable):
    """An dataclass with added serialize/deserialize methods.
    Values stored in the fields of the dataclass are not type checked, but must be primatives/serializable for the serialize
    method to return valid results.
    """


    @classmethod
    def _typeOfFieldNamed(cls, fieldName: str) -> Any:
        """Get the type annotation for the field with the given name.

        :return: The type of the field called `fieldName`, or `dataclasses._MISSING_TYPE` if no type was given for the field
        :rtype: type
        """
        return cls.__dataclass_fields__[fieldName].type # type: ignore


    @classmethod
    def _hasISerializableField(cls) -> bool:
        """Decide whether this class has any fields which are Serializable

        :return: True if at least one field is annotated as a Serializable type, False otherwise
        :rtype: bool
        """
        return any(issubclass(cls._typeOfFieldNamed(k), SerializableType) for k in cls.__dataclass_fields__) # type: ignore

    
    def serialize(self, deepTypeChecking: bool = False, **kwargs) -> Dict[str, PrimativeType]:
        """Serialize this object into a dictionary, to be recreated completely.

        :param bool deepTypeChecking: Whether to ensure serializability of member objects recursively (Default False)
        :return: A dictionary mapping field names to serialized values
        :rtype: Dict[str, PrimativeType]
        """
        data: Dict[str, PrimativeType] = {}

        for k in self.__dataclass_fields__: # type: ignore
            v = getattr(self, k)
            if isinstance(v, SerializableType):
                data[k] = v.serialize(**kwargs)
            elif deepTypeChecking and not objectIsDeepSerializable(v):
                raise TypeError(f"Field '{k}' is of non-serializable type: {type(v).__name__}")
            elif not deepTypeChecking and not objectIsShallowSerializable(v):
                raise TypeError(f"Field '{k}' is of non-serializable type, or has a non-serializable member. Type of {k}: {type(v).__name__}")
            else:
                data[k] = v

        return data


    @classmethod
    def deserialize(cls, data, deserializeValues: bool = True, **kwargs) -> "SerializableDataClass":
        """Recreate a serialized SerializableDataClass object. If `deserializeValues` is `True`,
        values fields which are serializable types will be automatically deserialized.

        :param Dict[str, PrimativeType] data: A dictionary mapping field names to values.
        :param bool deserializeValues: Whether to automatically deserialize serialized Serializable fields (Default True)
        :return: A new object as specified by data
        :rtype: SerializableDataClass
        """
        if not isinstance(data, dict):
            raise TypeError(f"Invalid type for parameter data. Expected Dict[str, PrimativeType], received {type(data).__name__}")

        if deserializeValues and cls._hasISerializableField():
            for k, v in data.items():
                if not isinstance(k, str):
                    raise TypeError(f"Invalid serialized {cls.__name__} key '{k}' Expected str, received {type(data).__name__}")
                if issubclass(cls._typeOfFieldNamed(k), SerializableType) and not isinstance(v, SerializableType):
                    data[k] = cls._typeOfFieldNamed(k).deserialize(v, **kwargs)
            
            data = cast(Dict[str, Any], data)

        return cls(**data **kwargs) # type: ignore
    