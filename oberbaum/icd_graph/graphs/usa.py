import logging
from dataclasses import dataclass
from pathlib import Path

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
            # print(f"Capítulo: {chapter}")

            for block_element in chapter_element.findall("section"):
                block = block_element.attrib.get("id")
                # print(f"  Seção: {block_element.findtext('desc')} {block_element.attrib.get('id')}")

                for diag_element in block_element.findall("diag"):
                    code = diag_element.findtext("name")
                    code = code.replace(".", "")
                    description = diag_element.findtext("desc")
                    self.add_or_update_code(
                        code,
                        chapter,
                        block,
                        three_char_category=code[:3],
                        description=description,
                    )
                    # connect first code after the block (expected to be a 3-char code)
                    self.connect_block_three_char_category(block, code)

                    def recursively_walk_codes(internal_diag_element, level=2):
                        # TODO receive previous code and connect them
                        code = internal_diag_element.findtext("name")
                        code = code.replace(".", "")
                        description = internal_diag_element.findtext("desc")
                        self.add_or_update_code(
                            code,
                            chapter,
                            block,
                            three_char_category=code[:3],
                            description=description,
                        )
                        # print("    " * level + f"Diag ({level}) {code} - {description}")

                        for sub_codes in internal_diag_element.findall("diag"):
                            recursively_walk_codes(sub_codes, level + 1)

                    recursively_walk_codes(diag_element)
            # break

            # FIXME self.connect_codes_recursively(code)

        del self._raw_data
