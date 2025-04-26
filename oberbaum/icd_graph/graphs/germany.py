from dataclasses import dataclass

from oberbaum.icd_graph.graphs.who import WHOICDGraph


@dataclass
class ICD10GMGraph(WHOICDGraph):
    """Class for representing the ICD-10-GM structure as a graph.

    Source:
    https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html
    """

    year: int = 2025
    version_name: str = "icd-10-gm"
    _chapters_filename: str = "icd10gm2025syst_kapitel.txt"
    _block_filename: str = "icd10gm2025syst_gruppen.txt"
    _codes_filename: str = "icd10gm2025syst_kodes.txt"
