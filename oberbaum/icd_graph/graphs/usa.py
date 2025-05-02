import logging
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
from lxml import etree

from oberbaum.icd_graph.graphs.base import ICDGraph

logger = logging.getLogger(__name__)


@dataclass
class ICD10CMGraph(ICDGraph):
    """Class for representing the USA ICD-10-CM structure as a graph.

    Source:
    https://www.cdc.gov/nchs/icd/icd-10-cm/index.html
    https://www.cdc.gov/nchs/icd/icd-10-cm/files.html
    """

    year: int = 2025
    version_name: str = "icd-10-cm"
    _seventh_chars_per_code: dict = field(default_factory=dict)
    _raw_data = None

    def load_initial_data(self):
        codes_file = Path(self.files_dir) / "icd10cm-tabular-April-2025.xml"
        # create an XML parser with entity resolution and network access disabled for security
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        self._raw_data = etree.parse(codes_file, parser)

    def add_chapters(self):
        mapping = {
            "name": "chapter_code",
            "desc": "chapter_name",
            "includes": "description",
        }
        for element in self._raw_data.findall("chapter"):
            attributes = {}
            element_children = list(element.iterchildren())
            start = None
            end = None
            for child in element_children:
                if mapping.get(child.tag):
                    text = child.text
                    if child.tag == "includes":
                        text = child.findtext("note")
                    attributes[mapping[child.tag]] = text

                if child.tag == "sectionIndex" and child.getchildren():
                    start = child.getchildren()[0].attrib.get("first")
                    end = child.getchildren()[-1].attrib.get("last")

            self.add_or_update_chapter(
                attributes["chapter_code"],
                attributes["chapter_name"],
                start,
                end,
                attributes.get("description"),
            )

    def add_blocks(self):
        for element in self._raw_data.findall(".//chapter/sectionIndex/sectionRef"):
            start = element.attrib.get("first")
            end = element.attrib.get("last")
            title = element.text.strip()
            chapter_code = element.getparent().getparent().find("./name").text
            block_name = self.add_or_update_block(start, end, chapter_code, title)
            self.connect_chapter_block(chapter_code, block_name)

    def add_codes(self):
        for chapter_element in self._raw_data.findall("chapter"):
            chapter = chapter_element.findtext("name")

            for block_element in chapter_element.findall("section"):
                block = block_element.attrib.get("id")

                three_char_category = None
                for diag_element in block_element.findall("diag"):
                    extra_data = {}
                    # get the current code
                    original_code = diag_element.findtext("name")
                    code = original_code.replace(".", "")
                    description = diag_element.findtext("desc")

                    # handle 3-char code
                    is_three_char_code = len(original_code) == 3 and "." not in code
                    if is_three_char_code:
                        three_char_category = code
                        # connect first code after the block (expected to be a 3-char code)
                        self.connect_block_three_char_category(block, code)

                    self._store_seventh_char_info(diag_element, code)
                    extra_data["seventh_char_info"] = self._seventh_chars_per_code.get(
                        code
                    )

                    # need to do this because the seven chars are not created as codes automatically
                    self.add_or_update_code(
                        code,
                        chapter,
                        block,
                        three_char_category=three_char_category,
                        description=description,
                        **extra_data,
                    )

                    # only the code in the file can be traversed
                    self._recursively_walk_codes(
                        diag_element, code, chapter, block, three_char_category
                    )

        for original_code, seventh_char_info in self._seventh_chars_per_code.items():
            # this means that all descendants of the code have the same seventh char
            descendants = nx.descendants(self._graph, original_code)
            codes_with_the_seventh = [
                code for code in descendants if self.is_code(code)
            ]
            # FIXME needs some clarification of when include the original code or not. Example: S52211
            codes_with_the_seventh.append(original_code)

            original_code_data = self.get(original_code)
            for code_with_the_seventh in codes_with_the_seventh:
                for seventh_char, seventh_char_description in seventh_char_info.items():
                    created_code_name = self._create_seventh_char_code_name(
                        code_with_the_seventh, seventh_char
                    )
                    # connecting with the original code, inspired by the browser tool
                    # https://icd10cmtool.cdc.gov/
                    extra_data = {
                        "seventh_char": seventh_char,
                        "seventh_char_description": seventh_char_description,
                    }
                    created_code_name = self.add_or_update_code(
                        created_code_name,
                        original_code_data["chapter"],
                        original_code_data["block"],
                        three_char_category=original_code_data["three_char_category"],
                        description=original_code_data["description"],
                        **extra_data,
                    )
                    self.connect_codes(original_code, created_code_name)

        del self._raw_data

    def _store_seventh_char_info(self, element, code):
        if element.find("sevenChrNote") is not None:
            for extension in element.findall(".//sevenChrDef/extension"):
                self._seventh_chars_per_code.setdefault(code, {}).update(
                    {extension.attrib.get("char"): extension.text}
                )
        return

    def get_seventh_char_info(self, code):
        if not self._seventh_chars_per_code.get(code):
            for predecessor in self.predecessors(code):
                if self._seventh_chars_per_code.get(predecessor):
                    self._seventh_chars_per_code[code] = (
                        self._seventh_chars_per_code.get(predecessor)
                    )
                    break
        return self._seventh_chars_per_code.get(code, {})

    def _recursively_walk_codes(
        self,
        internal_diag_element,
        previous_code,
        chapter,
        block,
        three_char_category,
        level=2,
    ):
        code = internal_diag_element.findtext("name").replace(".", "")
        created_code = self.add_or_update_code(
            code,
            chapter,
            block,
            three_char_category,
            internal_diag_element.findtext("desc"),
        )
        self._store_seventh_char_info(internal_diag_element, code)

        self.connect_codes(previous_code, created_code)
        for sub_codes in internal_diag_element.findall("diag"):
            self._recursively_walk_codes(
                sub_codes, created_code, chapter, block, three_char_category, level + 1
            )

    @staticmethod
    def _create_seventh_char_code_name(code: str, seventh_char: str) -> str:
        """Create a code with a seventh character.

        # FIXME 7th char is dealt differently
        # for each sevenChrDef, add extension char
        # TODO check the diag that have the "placeholder" tag and add the 7th char
        Args:
            code (str): The original code.
            seventh_char (str): The seventh character to add.

        Returns:
            str: The new code with the seventh character.
        """
        if not seventh_char or len(seventh_char) != 1:
            return code

        difference = 6 - len(code)
        placeholder = ""
        if difference > 0:  # our goal is to reach 7 chars
            placeholder = difference * "X"

        return f"{code}{placeholder}{seventh_char}"
