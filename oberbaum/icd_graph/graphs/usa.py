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
        # sectionRef
        logger.info("Blocks will be added during the code creation step.")

    def add_codes(self):
        del self._raw_data
