import keyword
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Union, TextIO, Callable, Dict, Iterator, Set
import logging

import click
from linkml_runtime.linkml_model import linkml_files
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import URIRef

import linkml
from linkml.generators import JAVA_GEN_VERSION
import linkml_runtime.linkml_model.types as linkml_types
from linkml_runtime.linkml_model.meta import SchemaDefinition, SlotDefinition, ClassDefinition, ClassDefinitionName, \
    SlotDefinitionName, DefinitionName, Element, TypeDefinition, Definition, EnumDefinition, PermissibleValue, TypeDefinition
from linkml_runtime.utils.formatutils import camelcase, underscore, be, wrapped_annotation, split_line, sfx, lcamelcase
from linkml.utils.generator import Generator, shared_arguments
from linkml.utils.ifabsent_functions import ifabsent_value_declaration, ifabsent_postinit_declaration, \
    default_curie_or_uri
from linkml_runtime.utils.metamodelcore import builtinnames


SAFE_NAME = str
TYPE_EXPRESSION = str
ANNOTATION = str
PACKAGE = str

@dataclass
class OODocument:
    """
    A collection of one or more OO classes
    """
    name: SAFE_NAME
    package: PACKAGE = None
    source_schema: SchemaDefinition = None
    classes: List["OOClass"] = field(default_factory=lambda: [])
    imports: List[str] = field(default_factory=lambda: [])


@dataclass
class OOField:
    """
    A field belonging to an OO class that corresponds to a LinkML class slot
    """
    name: SAFE_NAME
    range: TYPE_EXPRESSION = None
    annotations: List[ANNOTATION] = field(default_factory=lambda: [])
    source_slot: SlotDefinition = field(default_factory=lambda: [])

@dataclass
class OOClass:
    """
    An object-oriented class
    """
    name: SAFE_NAME
    is_a: Optional[SAFE_NAME] = None
    mixins: List[SAFE_NAME] = field(default_factory=lambda: [])
    fields: List[OOField] = field(default_factory=lambda: [])
    annotations: List[ANNOTATION] = field(default_factory=lambda: [])
    package: PACKAGE = None
    source_class: ClassDefinition = None

class OOCodeGenerator(Generator):
    package: PACKAGE = "example"
    java_style = True

    def get_class_name(self, cn):
        return camelcase(cn)

    def get_slot_name(self, sn):
        if self.java_style:
            safe_sn = lcamelcase(sn)
        else:
            safe_sn = underscore(sn)
        return safe_sn

    def map_type(self, t: TypeDefinition) -> str:
        return t.base

    def make_multivalued(self, range: str) -> str:
        return f'List<{range}>'

    def create_documents(self) -> List[OODocument]:
        """
        Currently hardcoded for java-style
        :return:
        """
        sv: SchemaView
        sv = self.schemaview
        docs = []
        for cn in sv.all_class(imports=False):
            c = sv.get_class(cn)
            safe_cn = camelcase(cn)
            oodoc = OODocument(name=safe_cn, package=self.package, source_schema=sv.schema)
            docs.append(oodoc)
            ooclass = OOClass(name=safe_cn, package=self.package, fields=[], source_class=c)
            # currently hardcoded for java style, one class per doc
            oodoc.classes = [ooclass]
            if c.is_a:
                ooclass.is_a = self.get_class_name(c.is_a)
                parent_slots = sv.class_slots(c.is_a)
            else:
                parent_slots = []
            for sn in sv.class_slots(cn):
                if sn in parent_slots:
                    # TODO: overrides
                    continue
                safe_sn = self.get_slot_name(sn)
                slot = sv.induced_slot(sn, cn)
                range = slot.range
                if range is None:
                    # TODO: schemaview should infer this
                    range = sv.schema.default_range
                if range is None:
                    range = 'string'
                if range in sv.all_class():
                    range = self.get_class_name(range)
                elif range in sv.all_type():
                    t = sv.get_type(range)
                    range = self.map_type(t)
                elif range in sv.all_enum():
                    range = sv.get_type(linkml_types.String)
                else:
                    raise Exception(f'Unknown range {range}')
                if slot.multivalued:
                    range = self.make_multivalued(range)
                oofield = OOField(name=safe_sn, source_slot=slot, range=range)
                ooclass.fields.append(oofield)
        return docs








