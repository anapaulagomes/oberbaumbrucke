import logging
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from oberbaum.icd_graph.graphs.base import ICDGraph

logger = logging.getLogger(__name__)


@dataclass
class ICD10CMGraph(ICDGraph):
    """Class for representing the USA ICD-10-CM structure as a graph.

    Source:
    https://www.cdc.gov/nchs/icd/icd-10-cm/index.html
    https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2025-Update/icd10cm-table-index-April-2025.zip

    It does not create new nodes to represent the 7th character of the code,
    as in the CDC browser tool: https://icd10cmtool.cdc.gov/
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
            if start == end:
                continue
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

                    extra_data["seventh_char_info"] = self._seventh_chars_per_code.get(
                        code
                    )

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

        del self._raw_data

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
            **{"placeholder": bool(internal_diag_element.attrib.get("placeholder"))},
        )

        self.connect_codes(previous_code, created_code)
        for sub_codes in internal_diag_element.findall("diag"):
            self._recursively_walk_codes(
                sub_codes, created_code, chapter, block, three_char_category, level + 1
            )
