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

    def add_root_node(self):
        self.graph.add_node(self._root_node)

    def add_chapters(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def chapters(self):
        return nx.descendants(self.graph, self._root_node)


@dataclass
class WHOICDGraph(ICDGraph):
    """Class for representing the WHO ICD structure as a graph.

    The version implemented here is the 2019 and the files can be
    downloaded from: https://www.who.int/classifications/icd/en/
    """

    version_name: str = "icd-10-who"

    def add_chapters(self):
        chapters_file = Path(self.files_dir) / "icd102019syst_chapters.txt"
        for line in chapters_file.read_text().splitlines():
            chapter_code, chapter_name = line.split(";", 1)
            self.graph.add_node(chapter_code, name=chapter_name)
            self.graph.add_edge(self._root_node, chapter_code)


def get_graph(version: str, files_dir: str) -> ICDGraph:
    return WHOICDGraph(version_name=version, files_dir=files_dir)
