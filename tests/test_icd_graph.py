import networkx as nx
import pytest

from oberbaum.icd_graph import ICDGraph, get_graph, WHOICDGraph


@pytest.fixture
def chapters_file_dir(tmp_path):
    chapters_file = tmp_path / "icd102019syst_chapters.txt"
    chapters_file.write_text(
        "01;Certain infectious and parasitic diseases\n"
        "02;Neoplasms\n"
        "03;Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism\n"
        "04;Endocrine, nutritional and metabolic diseases\n"
        "05;Mental and behavioural disorders\n"
    )
    return str(tmp_path)


class TestWHOICD10Graph:
    def test_create_who_icd10_graph(self, chapters_file_dir):
        graph = WHOICDGraph(files_dir=chapters_file_dir)
        assert graph.version_name == "icd-10-who"
        assert isinstance(graph.graph, nx.DiGraph)

    def test_get_all_chapters(self, chapters_file_dir):
        graph = WHOICDGraph(files_dir=chapters_file_dir)
        chapters = graph.chapters()
        assert isinstance(chapters, set)
        assert len(chapters) == 5


class TestGetGraph:
    def test_get_graph_by_name(self, chapters_file_dir):
        graph = get_graph("icd-10-who", chapters_file_dir)
        assert isinstance(graph, ICDGraph)
        assert isinstance(graph, WHOICDGraph)
        assert graph.version_name == "icd-10-who"
