from dataclasses import dataclass
import json
from string import Template
from typing import Any

from dataclasses_json import DataClassJsonMixin

from . import api_types


@dataclass
class MetaData(DataClassJsonMixin):
    name: str = None
    dstPath: str = None
    modified: str = None


@dataclass
class WrappedType(DataClassJsonMixin):
    className: str = None
    metaData: MetaData = None
    data: dict = None

    def to_instance(self):
        class_ = getattr(api_types, self.className)
        return class_.from_json(json.dumps(self.data))

    def to_file(self, path_):
        with open(path_, 'w') as f:
            json.dump(json.loads(self.to_json()), f, indent=2)

    @staticmethod
    def createFromFile(path_, template_values=None, error_on_missing=True):
        with open(path_, 'r') as f:
            obj = json.dumps(json.load(f))
            if template_values:
                obj = Template(obj)
                if error_on_missing:
                    obj = obj.substitute(template_values)
                else:
                    obj = obj.safe_substitute(template_values)
            return WrappedType.from_json(obj)

    @staticmethod
    def create(instance: Any) -> 'WrappedType':
        # expects an instance of an api_type Class
        class_ = type(instance)
        return WrappedType(
            class_.__qualname__,
            MetaData(),
            json.loads(instance.to_json())
        )
