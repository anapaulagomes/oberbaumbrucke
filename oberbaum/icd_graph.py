import csv
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
from rich.console import Console
from rich.text import Text
from rich.tree import Tree

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
    _chapters: dict = field(default_factory=dict)
    _blocks: dict = field(default_factory=dict)
    _levels: dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the graph and add nodes and edges."""
        self._graph_ready = False
        self.add_root_node()
        self.add_chapters()
        self.add_blocks()
        self.add_codes()
        self._graph_ready = True

    def add_chapters(self):
        """Add chapters to the graph.

        The chapters should be added using the method `add_chapter`."""
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_codes(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_blocks(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_root_node(self):
        self.graph.add_node(self._root_node)

    def add_chapter(
        self, chapter_code, chapter_name=None, start=None, end=None, description=None
    ):
        data = {
            "start": start,
            "end": end,
            "name": chapter_name,
            "description": description,
            "type": "chapter",
        }
        self.graph.add_node(chapter_code, **data)
        del data["type"]
        self._chapters[chapter_code] = data
        self.graph.add_edge(self._root_node, chapter_code)

    def add_block(self, start, end, chapter_code=None, title=None):
        """Add blocks to the graph.

        If the chapter code is provided, it will be used to create the edge between chapter and block."""
        block_name = self.block_name(start, end)
        description = self.block_description(block_name, title)
        data = {
            "start": start,
            "end": end,
            "chapter_code": chapter_code,
            "name": title,
            "description": description,
            "type": "block",
        }
        self.graph.add_node(block_name, **data)
        del data["type"]
        self._blocks[block_name] = data

        parent_block = self.find_parent_block(block_name)
        if parent_block:
            if chapter_code:
                self.connect_chapter_block(
                    chapter_code, parent_block
                )  # chapter and block
            self.connect_blocks(parent_block, block_name)  # block and sub-block
            return
        if chapter_code:
            self.connect_chapter_block(chapter_code, block_name)

    def find_parent_block(self, block):
        """Find the parent of a given block.

        A block may be a child of a chapter or another block."""
        block_data = self.get(block)
        block_start_letter = block_data["start"][0]
        block_end_letter = block_data["end"][0]
        for current_block, current_data in self.blocks(data=True):
            if (
                current_data["start"][0] == block_start_letter
                and current_data["end"][0] == block_end_letter
            ):
                match_start = int(block_data["start"][1:]) >= int(
                    current_data["start"][1:]
                )
                match_end = int(current_data["end"][1:]) >= int(block_data["end"][1:])

                if block != current_block and (match_start and match_end):
                    return current_block
        return

    def get(self, node):
        """Get the data for a given element in the graph."""
        return self.graph.nodes[node]

    def add_code(
        self,
        code,
        chapter=None,
        block=None,
        three_char_category=None,
        description=None,
        title=None,
        **kwargs,
    ):
        data = {
            "chapter": chapter,
            "block": block,
            "three_char_category": three_char_category,
            "description": description,
            "name": title,
        }
        self.graph.add_node(code, **data, **kwargs)

    def connect_block_three_char_category(self, block, three_char_category):
        """Create the edge between chapter and block."""
        self.graph.add_edge(block, three_char_category)

    def connect_three_char_category_code(self, three_char_category, code):
        """Create the edge between chapter and block."""
        self.graph.add_edge(three_char_category, code)

    def connect_chapter_block(self, chapter_code, block_name):
        """Create the edge between chapter and block.

        If the chapter code is not present in the block, it will be added to the block node
        for convenience."""
        if not self.graph.nodes[block_name].get(chapter_code):
            # FIXME update_block()
            self.graph.nodes[block_name]["chapter_code"] = chapter_code
            self._blocks[block_name]["chapter_code"] = chapter_code

        self.graph.add_edge(chapter_code, block_name)

    def connect_blocks(self, block, sub_block):
        """Create the edge between chapter and block."""
        self.graph.add_edge(block, sub_block)
        self._blocks[sub_block]["main_block"] = block

    def chapters(self, roman_numerals=False, data=False):
        if data:
            return self._chapters.items()
        codes = list(self._chapters.keys())
        if roman_numerals:
            return [ROMAN_NUMERALS[int(code)] for code in codes]
        return codes

    def categories(self, from_block=None):
        """Get all categories in the graph."""
        all_categories = set()
        for block in self.blocks():
            if from_block and block != from_block:
                continue
            all_categories.update(nx.descendants(self.graph, block))
        return all_categories

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
        if self._graph_ready and not self._levels:
            layers = list(nx.bfs_layers(self.graph, self._root_node))
            self._levels = {
                level: layer for level, layer in enumerate(layers) if level != 0
            }
            return self._levels
        return self._levels

    def blocks(self, data=False):
        """Get all blocks in the graph."""
        if data:
            return self._blocks.items()
        return list(self._blocks.keys())

    @staticmethod
    def block_name(start, end):
        """Get the block name for a given start and end code."""
        return f"{start}-{end}"

    @staticmethod
    def block_description(node, description):
        """Get the block description for a given start and end code.

        Example: Intestinal infectious diseases (A00-A09)
        """
        return f"{description} ({node})"

    def three_char_codes(self):
        return self.codes_per_level()[3]

    def four_char_codes(self):
        return self.codes_per_level()[4]

    def export(self):
        gml_file = f"{self.version_name}.gml"
        graph_copy = self.graph.copy()
        graph_copy = self._from_none_to_empty(graph_copy, graph_copy.nodes(data=True))
        nx.write_gml(graph_copy, gml_file)
        return gml_file

    def predecessors(self, node, _track=None):
        if _track is None:
            _track = []
        result = nx.predecessor(self.graph, self._root_node, node)
        _track.extend(result)

        if not result:
            if self._root_node in _track:
                _track.remove(self._root_node)
            return _track
        return self.predecessors(result[0], _track)

    def _from_none_to_empty(self, a_graph, data_dict):
        """Convert all None values to empty strings in a dictionary."""
        for item, data in data_dict:
            if item == self._root_node:
                continue
            for key, value in data.items():
                if value is None:
                    data[key] = ""
        return a_graph

    def find_chapter(self, code):
        """Find the chapter for a given code.

        Every chapter has a start and end category code.
        Use this method to find the chapter for a given code."""
        return self._find_in(self.chapters(data=True), code)

    def find_block(self, code, include_subblocks=False):
        """Find the block for a given code.

        Every block has a start and end category code.
        Use this method to find the block for a given code."""
        return self._find_in(self.blocks(data=True), code, include_subblocks)

    def _find_in(self, data_set: dict, code: str, return_all=False):
        letter = code[0]
        found = []
        for item, data in data_set:
            start = data.get("start")
            end = data.get("end")
            if not start and not end:
                continue

            number = int(code[1:3])
            start_number = int(start[1:])
            end_number = int(end[1:])
            start_letter = start[0]
            end_letter = end[0]

            if letter == start_letter == end_letter:
                if start_number <= number <= end_number:
                    if not return_all:
                        return item

                    found.append(item)
            else:
                if letter == start_letter:
                    if number >= start_number:
                        if not return_all:
                            return item

                        found.append(item)
                elif letter == end_letter:
                    if number <= end_number:
                        if not return_all:
                            return item

                        found.append(item)
                else:
                    if start_letter < letter < end_letter:
                        if not return_all:
                            return item

                        found.append(item)

        if not return_all:
            return None

        return found


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
            self.add_chapter(chapter_code, chapter_name)

    def add_blocks(self):
        blocks_file = Path(self.files_dir) / "icd102019syst_groups.txt"
        for line in blocks_file.read_text().splitlines():
            start, end, chapter_code, title = line.split(";")
            self.add_block(start, end, chapter_code, title)

    def add_codes(self):
        """Add all codes to the graph.

        Assumption: Use the first three digits of the code to find the block,
        given that the file has some misplaced codes.
        Example: code D56.1 have as first_3_block_code 55 instead of 56, displayed
        in https://icd.who.int/browse10/2016/en#/D56.1.

        Fields:
            hierarchy_level;tree_place;terminal_node_type;chapter_number;
            first_3_block_code;code;code_without_asterisk;code_without_dot;
            full_title;title;subtitle;code_type;mortality1;
            mortality2;mortality3;mortality4;morbidity_list
        """
        codes_file = Path(self.files_dir) / "icd102019syst_codes.txt"
        for line in codes_file.read_text().splitlines():
            fields = line.split(";")
            code = fields[7]  # 3 or 4 char category
            three_char_category = code[:3]
            block = self.find_block(three_char_category)
            chapter = fields[3]
            description = fields[8]
            title = fields[9]
            extra_data = {"subtitle": fields[10], "formatted_code": fields[5]}

            self.add_code(
                code,
                chapter,
                block,
                three_char_category,
                description,
                title,
                **extra_data,
            )
            self.connect_chapter_block(chapter, block)

            # TODO update block, sub-block, chapter?

            if len(code) == 3:
                self.connect_block_three_char_category(block, code)
            else:
                self.connect_three_char_category_code(three_char_category, code)


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
            chapter_code = line["NUMCAP"]
            chapter_name = line["DESCRABREV"]
            start = line["CATINIC"]
            end = line["CATFIM"]
            description = line["DESCRICAO"]
            self.add_chapter(chapter_code, chapter_name, start, end, description)

    def add_blocks(self):
        blocks_file_dir = f"{self.files_dir}/CID-10-GRUPOS.CSV"
        reader = csv.DictReader(
            open(blocks_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            start = line["CATINIC"]
            end = line["CATFIM"]
            title = line["DESCRABREV"]
            self.add_block(start, end, title=title)

    def add_codes(self):
        """Add all codes to the graph."""
        codes_file_dir = f"{self.files_dir}/CID-10-SUBCATEGORIAS.CSV"
        reader = csv.DictReader(
            open(codes_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            # FIXME text encoding
            code = line["SUBCAT"]
            description = line["DESCRICAO"]
            title = line["DESCRABREV"]
            chapter = self.find_chapter(code)
            blocks = self.find_block(code, include_subblocks=True)
            block = blocks[0]
            sub_block = block
            if len(blocks) > 1:
                sub_block = blocks[1]
            three_char_category = code[:3]  # also from CID-10-CATEGORIAS.CSV

            # TODO let each item have its own data

            self.add_code(
                code,
                chapter,
                block,
                three_char_category,
                description,
                title,
                sub_block=sub_block,
            )
            self.connect_chapter_block(chapter, block)
            # block and sub-block are already connected due to groups' file structure
            self.connect_block_three_char_category(sub_block, three_char_category)
            self.connect_three_char_category_code(three_char_category, code)


def print_graph(graph, root_node=None):
    """
    Print an ICDGraph in the terminal.

    Args:
        graph: A ICDGraph that is a tree
        root_node: The root node to start from (if None, will try to find a root)
    """
    console = Console()
    root_node = root_node or graph._root_node
    rich_tree = Tree(Text(str(root_node), style="bold"))
    G = graph.graph

    def add_children(parent_node, rich_parent):
        for child in G.successors(parent_node):
            child_text = Text(child)
            child_text.stylize("gray")
            rich_child = rich_parent.add(child_text)
            add_children(child, rich_child)

    add_children(root_node, rich_tree)
    console.print(rich_tree)
