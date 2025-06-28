import csv
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from oberbaum.icd_graph.graphs.base import ICDGraph
from oberbaum.icd_graph.graphs.who import WHOICDGraph


@dataclass
class CID10Graph2008(ICDGraph):
    """Class for representing the Brazilian ICD-10 version structure as a graph.

    The version implemented here is the 2008.
    Files for download: http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip
    ICD-10 metadata Format: http://www2.datasus.gov.br/cid10/V2008/cid10.htm
    Guidelines: https://www.saude.df.gov.br/documents/37101/0/E_book_CID_10__2_.pdf
    """

    year: int = 2008
    version_name: str = "cid-10-bra-2008"

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
            self.add_or_update_chapter(
                chapter_code, chapter_name, start, end, description
            )

    def add_blocks(self):
        blocks_file_dir = f"{self.files_dir}/CID-10-GRUPOS.CSV"
        reader = csv.DictReader(
            open(blocks_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            start = line["CATINIC"]
            end = line["CATFIM"]
            title = line["DESCRABREV"]
            block_name = self.add_or_update_block(start, end, title=title)
            self.connect_blocks_sub_blocks(block_name)

    def add_codes(self):
        """Add all codes to the graph."""
        categories_file_dir = f"{self.files_dir}/CID-10-CATEGORIAS.CSV"
        reader = csv.DictReader(
            open(categories_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            code = line["CAT"]
            description = line["DESCRICAO"]
            title = line["DESCRABREV"]
            chapter_code = self.find_chapter(code)
            blocks = self.find_block(code, include_subblocks=True)
            block = blocks[0]
            sub_block = None
            if len(blocks) > 1:
                sub_block = blocks[1]
            classification = line["CLASSIF"]
            extra_data = {"classification": classification}
            code = self.add_or_update_code(
                code,
                chapter_code,
                sub_block or block,
                description=description,
                title=title,
                **extra_data,
            )
            self.connect_chapter_block(chapter_code, block)
            self.connect_block_three_char_category(sub_block or block, code)

        codes_file_dir = f"{self.files_dir}/CID-10-SUBCATEGORIAS.CSV"
        reader = csv.DictReader(
            open(codes_file_dir, "r", encoding="iso-8859-1"), delimiter=";"
        )
        for line in reader:
            # FIXME text encoding
            code = line["SUBCAT"]
            description = line["DESCRICAO"]
            title = line["DESCRABREV"]
            chapter_code = self.find_chapter(code)
            blocks = self.find_block(code, include_subblocks=True)
            block = blocks[0]
            sub_block = None
            if len(blocks) > 1:
                sub_block = blocks[1]

            self.add_or_update_code(
                code,
                chapter_code,
                sub_block or block,
                description=description,
                title=title,
            )

            self.connect_codes_recursively(code)
