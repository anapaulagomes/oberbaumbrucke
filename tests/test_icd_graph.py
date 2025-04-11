import networkx as nx
import pytest

from oberbaum.icd_graph import ICDGraph, get_graph, WHOICDGraph


@pytest.fixture
def icd_file_dir(tmp_path):
    chapters_file = tmp_path / "icd102019syst_chapters.txt"
    chapters_file.write_text(
        "01;Certain infectious and parasitic diseases\n"
        "02;Neoplasms\n"
        "03;Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism\n"
        "04;Endocrine, nutritional and metabolic diseases\n"
        "05;Mental and behavioural disorders\n"
    )
    codes_file = tmp_path / "icd102019syst_codes.txt"
    codes_file.write_text(
        "3;N;X;01;A00;A00.-;A00;A00;Cholera;Cholera;;;001;4-002;3-003;2-001;1-002\n"
        "4;T;X;01;A00;A00.0;A00.0;A000;Cholera due to Vibrio cholerae 01, biovar cholerae;Cholera;Cholera due to Vibrio cholerae 01, biovar cholerae;;001;4-002;3-003;2-001;1-002\n"
        "4;T;X;01;A00;A00.1;A00.1;A001;Cholera due to Vibrio cholerae 01, biovar eltor;Cholera;Cholera due to Vibrio cholerae 01, biovar eltor;;001;4-002;3-003;2-001;1-002\n"
    )
    return str(tmp_path)


class TestWHOICD10Graph:
    def test_create_who_icd10_graph(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        assert graph.version_name == "icd-10-who"
        assert isinstance(graph.graph, nx.DiGraph)

    def test_get_all_chapters(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        chapters = graph.chapters()
        assert isinstance(chapters, set)
        assert len(chapters) == 5

    def test_add_chapters(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        assert len(graph.graph.nodes) == 6  # root and 5 chapters

    def test_add_codes(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)

        assert graph.graph.has_node("A00")
        assert graph.graph.has_node("A000")
        assert graph.graph.has_node("A001")
        assert graph.graph.has_edge("A00", "A000")
        assert graph.graph.has_edge("A00", "A001")


class TestGetGraph:
    def test_get_graph_by_name(self, icd_file_dir):
        graph = get_graph("icd-10-who", icd_file_dir)
        assert isinstance(graph, ICDGraph)
        assert isinstance(graph, WHOICDGraph)
        assert graph.version_name == "icd-10-who"
