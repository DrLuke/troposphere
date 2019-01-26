"""AWS Specification Resource Class

These classes parse an AWS CF specification as documented here:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification-format.html
"""

from typing import Dict, Union
from troposphere_gen.types import PrimitiveType, Subproperty, MapType, ListType


class Attribute():
    """Parsed attribute"""

    def __init__(self, name: str, attributedict: Dict) -> None:
        self.name: str = name
        self.item_type: Subproperty = None
        self.primitive_item_type: PrimitiveType = None
        self.primitive_type: PrimitiveType = None
        self.type: Union[Subproperty, ListType, MapType] = None

        self.parse(attributedict)

    def parse(self, attributedict: Dict) -> None:
        """Parse JSON attribute definition"""
        # Determine type
        if "PrimitiveType" in attributedict:
            self.primitive_type = PrimitiveType(attributedict["PrimitiveType"])
        elif "Type" in attributedict:
            if attributedict["Type"] == "List":
                if "PrimitiveItemType" in attributedict:
                    self.type = ListType(PrimitiveType(attributedict["PrimitiveItemType"]))
                elif "ItemType" in attributedict:
                    self.type = ListType(Subproperty(attributedict["ItemType"]))
            elif attributedict["Type"] == "Map":
                if "PrimitiveItemType" in attributedict:
                    self.type = MapType(PrimitiveType(attributedict["PrimitiveItemType"]))
                elif "ItemType" in attributedict:
                    self.type = MapType(Subproperty(attributedict["ItemType"]))
            else:
                self.type = Subproperty(attributedict["Type"])


class Property(Attribute):
    """Parsed property"""

    def __init__(self, name: str, propertydict: Dict) -> None:
        self.documentation: str = None
        self.duplicate_allowed: bool = None
        self.required: bool = None
        self._update_type: str = None
        self.properties: Dict[str, Property] = {}

        super(Property, self).__init__(name, propertydict)

    def parse(self, propertydict: Dict) -> None:
        """Parse JSON property definition"""
        self.documentation = propertydict["Documentation"]

        # If property contains subproperties, only parse those
        if "Properties" in propertydict:
            for name, subpropertydict in propertydict["Properties"].items():
                self.properties[name] = Property(name, subpropertydict)
            return

        self.update_type = propertydict["UpdateType"]
        self.required = propertydict["Required"]

        super(Property, self).parse(propertydict)

        if "DuplicatesAllowed" in propertydict:
            self.duplicate_allowed = propertydict["DuplicatesAllowed"]

    @property
    def update_type(self) -> str:
        return self._update_type

    @update_type.setter
    def update_type(self, update_type: str) -> None:
        if update_type in ["Immutable", "Mutable", "Conditional"]:
            self._update_type = update_type
        else:
            raise ValueError("Invalid update type: %s" % update_type)


class Resource():
    """Parsed resource"""

    def __init__(self, name: str, resourcedict: Dict) -> None:
        self.name: str = name
        self.documentation: str = None
        self.attributes: Dict[str, Attribute] = {}
        self.properties: Dict[str, Property] = {}

        self.parse(resourcedict)

    def parse(self, resourcedict: Dict) -> None:
        """Parse JSON resource definition"""
        self.documentation = resourcedict["Documentation"]

        for name, attributedict in resourcedict["Attributes"].items():
            self.attributes[name] = Attribute(name, attributedict)

        for name, propertydict in resourcedict["Properties"].items():
            self.properties[name] = Property(name, propertydict)
