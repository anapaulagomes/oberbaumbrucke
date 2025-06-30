import pytest

from oberbaum.icd_graph.graphs.germany import ICD10GMGraph
from oberbaum.icd_graph.graphs.who import WHOICDGraph
from oberbaum.icd_graph.match import is_uphill_match


class TestUphillMatch:
    @pytest.mark.parametrize(
        "a_code,another_code,expected",
        [
            ("B1813", "B1800", True),
            ("B180", "B1800", False),
            ("C8870", "C887", True),
        ],
        ids=["same_length", "shorter_code", "example_from_maier_et_al_2018"],
    )
    def test_is_uphill_match(
        self,
        a_code,
        another_code,
        expected,
        real_icd10_who_file_dir,
        real_icd10_gm_file_dir,
    ):
        G = ICD10GMGraph(files_dir=real_icd10_gm_file_dir)
        W = WHOICDGraph(files_dir=real_icd10_who_file_dir)

        assert is_uphill_match(G, a_code, W, another_code) is expected, (
            f"{a_code} ~ {another_code}"
        )
