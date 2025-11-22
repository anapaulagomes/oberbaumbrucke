from oberbaum.graphs.brazil import CID10Graph
from oberbaum.graphs.who import WHOICDGraph


class TestLoadGraphFromFile:
    def test_load_graph_from_file(self):
        graph = CID10Graph(gml_filepath="tests/fixtures/subgraph_B180_cid10.gml")

        assert graph.chapters()
        assert graph.blocks()
        assert graph.codes()

    def test_is_code(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)

        assert graph.is_code("1") is False
        assert graph.is_code("A92-A99") is False
        assert graph.is_code("A92") is False
        assert graph.is_code("A") is False
        assert graph.is_code("J10") is False
        assert graph.is_code("A929") is True

    def test_display_category_and_char_len_for_codes(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)

        assert graph.get("1").get("char_len") is None
        assert graph.get("1").get("category") is None
        assert graph.get("A92-A99").get("char_len") is None
        assert graph.get("A92-A99").get("category") is None
        assert graph.get("J10")["char_len"] == 3
        assert graph.get("J10")["category"] == "category"
        assert graph.get("A929")["char_len"] == 4
        assert graph.get("A929")["category"] == "subcategory"
        assert graph.get("B1810")["char_len"] == 5
        assert graph.get("B1810")["category"] == "code"
