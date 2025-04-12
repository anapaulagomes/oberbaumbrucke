from abc import ABC
from dataclasses import dataclass
from pathlib import Path

import networkx as nx


@dataclass
class ICDGraph(ABC):
    """Class for representing the ICD structure as a graph."""

    files_dir: str
    version_name: str
    graph: nx.DiGraph = nx.DiGraph()
    _root_node: str = "root"

    def __post_init__(self):
        self.add_root_node()
        self.add_chapters()
        self.add_codes()

    def add_chapters(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_codes(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_root_node(self):
        self.graph.add_node(self._root_node)

    def chapters(self):
        root_descendants = list(
            nx.dfs_tree(
                self.graph, source=self._root_node, depth_limit=1, sort_neighbors=sorted
            )
        )
        root_descendants.remove(self._root_node)
        return root_descendants

    def codes(self, from_chapter=None):
        all_codes = set()
        for chapter in self.chapters():
            if from_chapter is None:  # all codes
                all_codes.update(nx.descendants(self.graph, chapter))
                continue

            if chapter == from_chapter:  # specific chapter
                all_codes.update(nx.descendants(self.graph, chapter))
                break
        return all_codes

    def levels(self):
        layers = list(nx.bfs_layers(self.graph, self._root_node))
        return {
            level: len(layer) for level, layer in enumerate(layers) if level != 0
        }  # remove root node

    def export(self):
        gml_file = f"{self.version_name}.gml"
        nx.write_gml(self.graph, gml_file)
        return gml_file


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
            self.graph.add_node(chapter_code, name=chapter_name)
            self.graph.add_edge(self._root_node, chapter_code)

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
            data = {
                "chapter": fields[3],
                "block": fields[4],
                "formatted_code": fields[5],
                "code": fields[7],  # code without dot
                "full_title": fields[8],
                "title": fields[9],
                "subtitle": fields[10],
            }
            self.graph.add_node(data["code"], name=data["full_title"], **data)
            self.graph.add_edge(data["chapter"], data["block"])
            self.graph.add_edge(data["block"], data["code"])


def get_graph(version: str, files_dir: str) -> ICDGraph:
    return WHOICDGraph(version_name=version, files_dir=files_dir)
