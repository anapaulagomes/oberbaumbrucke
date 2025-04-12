import csv
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx


ROMAN_NUMERALS = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
    13: "XIII",
    14: "XIV",
    15: "XV",
    16: "XVI",
    17: "XVII",
    18: "XVIII",
    19: "XIX",
    20: "XX",
    21: "XXI",
    22: "XXII",
}


@dataclass
class ICDGraph(ABC):
    """Class for representing the ICD structure as a graph."""

    files_dir: str
    version_name: str
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    _root_node: str = "root"

    def __post_init__(self):
        self.add_root_node()
        self.add_chapters()
        self.add_blocks()
        self.add_codes()

    def add_chapters(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_codes(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_blocks(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_root_node(self):
        self.graph.add_node(self._root_node)

    def chapters(self, roman_numerals=False):
        codes = self.codes_per_level()[1]  # chapters are at level 1
        if roman_numerals:
            return [ROMAN_NUMERALS[int(code)] for code in codes]
        return codes

    def codes(self, from_chapter=None, exclude_3_char=True):
        all_codes = set()
        for chapter in self.chapters():
            if from_chapter is None:  # all codes
                all_codes.update(nx.descendants(self.graph, chapter))
                continue

            if chapter == from_chapter:  # specific chapter
                all_codes.update(nx.descendants(self.graph, chapter))
                break

        # remove blocks and chapters
        if exclude_3_char:
            all_codes = {
                node
                for node in all_codes
                if self.graph.out_degree(node) == 0
                and self.graph.in_degree(node) == 1  # leaf
            }
        return all_codes

    def levels(self):
        layers = self.codes_per_level()
        return {level: len(layer) for level, layer in layers.items()}

    def codes_per_level(self):
        layers = list(nx.bfs_layers(self.graph, self._root_node))
        return {level: layer for level, layer in enumerate(layers) if level != 0}

    def blocks(self):
        """Get all blocks in the graph."""
        return self.codes_per_level()[2]  # blocks are at level 2

    def three_char_codes(self):
        return self.codes_per_level()[3]

    def four_char_codes(self):
        return self.codes_per_level()[4]

    def export(self):
        gml_file = f"{self.version_name}.gml"
        nx.write_gml(self.graph, gml_file)
        return gml_file

    def find_chapter(self, code):
        """Find the chapter for a given code.

        Every chapter has a start and end category code.
        Use this method to find the chapter for a given code."""
        letter = code[0]
        for chapter in self.chapters():
            start = self.graph.nodes[chapter]["start"]
            end = self.graph.nodes[chapter]["end"]
            if start.startswith(letter) or end.startswith(letter):
                number = code[1:]
                start_number = start[1:]
                end_number = end[1:]
                if start_number <= number <= end_number:
                    return chapter
        return

    def find_block(self, code):
        """Find the block for a given code.

        Every block has a start and end category code.
        Use this method to find the block for a given code."""
        letter = code[0]
        for item, data in self.graph.nodes(data=True):
            if not data.get("is_block"):
                continue
            start = data["start"]
            end = data["end"]
            if start.startswith(letter) or end.startswith(letter):
                number = code[1:]
                start_number = start[1:]
                end_number = end[1:]
                if start_number <= number <= end_number:
                    return item
        return


@dataclass
class WHOICDGraph(ICDGraph):
    """Class for representing the WHO ICD structure as a graph.

    The version implemented here is the 2019.
    Files for download: https://icdcdn.who.int/icd10/meta/icd102019enMeta.zip
    ICD-10 metadata Format: https://icdcdn.who.int/icd10/metainfo.html
    Guidelines: https://icd.who.int/browse10/Content/statichtml/ICD10Volume2_en_2019.pdf
    """

    version_name: str = "icd-10-who"

    def add_chapters(self):
        """The instructions mention 21 chapters but the file has 22."""
        chapters_file = Path(self.files_dir) / "icd102019syst_chapters.txt"
        for line in chapters_file.read_text().splitlines():
            chapter_code, chapter_name = line.split(";", 1)
            self.graph.add_node(chapter_code, name=chapter_name)  # FIXME make it int
            self.graph.add_edge(self._root_node, chapter_code)

    def add_blocks(self):
        blocks_file = Path(self.files_dir) / "icd102019syst_groups.txt"
        for line in blocks_file.read_text().splitlines():
            start, end, block_code, title = line.split(";")
            # e.g. Intestinal infectious diseases (A00-A09)
            name = f"{title} ({start}-{end})"
            node = f"{start}-{end}"
            self.graph.add_node(
                node, name=name, start=start, end=end, title=title, is_block=True
            )

    def add_codes(self):
        """Add all codes to the graph.

        Fields:
            hierarchy_level;tree_place;terminal_node_type;chapter_number;
            first_3_block_code;code;code_without_asterisk;code_without_dot;
            full_title;title;subtitle;code_type;mortality1;
            mortality2;mortality3;mortality4;morbidity_list
        """
        codes_file = Path(self.files_dir) / "icd102019syst_codes.txt"
        for line in codes_file.read_text().splitlines():
            fields = line.split(";")
            block = self._find_block(fields[4])
            data = {
                "chapter": fields[3],
                "block": block,
                "three_char_category": fields[4],
                "formatted_code": fields[5],
                "code": fields[7],  # 3 or 4 char category
                "full_title": fields[8],
                "title": fields[9],
                "subtitle": fields[10],
            }
            self.graph.add_node(data["code"], name=data["full_title"], **data)
            self.graph.add_edge(data["chapter"], data["block"])

            if len(data["code"]) == 3:
                self.graph.add_edge(data["block"], data["code"])
            else:
                self.graph.add_edge(data["three_char_category"], data["code"])

    def _find_block(self, start):
        for node in self.graph.nodes:
            if node.startswith(start):
                return node
        return


def get_graph(version: str, files_dir: str) -> ICDGraph:
    subclasses = {
        subclass.version_name: subclass for subclass in ICDGraph.__subclasses__()
    }
    return subclasses[version](files_dir=files_dir)


@dataclass
class CID10Graph(ICDGraph):
    """Class for representing the Brazilian ICD-10 version structure as a graph.

    The version implemented here is the 2019.
    Files for download: http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip
    ICD-10 metadata Format: http://www2.datasus.gov.br/cid10/V2008/cid10.htm
    Guidelines: https://www.saude.df.gov.br/documents/37101/0/E_book_CID_10__2_.pdf
    """

    version_name: str = "cid-10-bra"

    def add_chapters(self):
        """The instructions mention 21 chapters but the file has 22."""
        chapter_file_dir = f"{self.files_dir}/CID-10-CAPITULOS.CSV"
        reader = csv.DictReader(
            open(chapter_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            chapter_code = line["NUMCAP"]  # FIXME make it int
            chapter_name = line["DESCRABREV"]
            data = {
                "start": line["CATINIC"],
                "end": line["CATFIM"],
                "description": line["DESCRICAO"],
                "is_chapter": True,
            }
            self.graph.add_node(chapter_code, name=chapter_name, **data)
            self.graph.add_edge(self._root_node, chapter_code)

    def add_blocks(self):
        blocks_file_dir = f"{self.files_dir}/CID-10-GRUPOS.CSV"
        reader = csv.DictReader(
            open(blocks_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            data = {
                "start": line["CATINIC"],
                "end": line["CATFIM"],
                "description": line["DESCRICAO"],
                "title": line["DESCRABREV"],
                "is_block": True,  # TODO maybe type=block?
            }
            node = f"{data['start']}-{data['end']}"  # TODO extract to a function
            name = f"{line['DESCRABREV']} ({node})"  # TODO extract to a function
            self.graph.add_node(node, name=name, **data)

    def add_codes(self):
        """Add all codes to the graph."""
        codes_file_dir = f"{self.files_dir}/CID-10-SUBCATEGORIAS.CSV"
        reader = csv.DictReader(
            open(codes_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            data = {
                "code": line["SUBCAT"],  # subcategory = 4 char
                "full_title": line["DESCRICAO"],
                "title": line["DESCRABREV"],
                "chapter": self.find_chapter(line["SUBCAT"]),
                "block": self.find_block(line["SUBCAT"]),
                "three_char_category": line["SUBCAT"][
                    :3
                ],  # also from CID-10-CATEGORIAS.CSV
            }
            self.graph.add_node(data["code"], name=data["full_title"], **data)
            self.graph.add_edge(data["chapter"], data["block"])
            self.graph.add_edge(data["block"], data["three_char_category"])
            self.graph.add_edge(data["three_char_category"], data["code"])

            # FIXME text encoding
