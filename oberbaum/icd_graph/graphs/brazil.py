import csv
import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from oberbaum.icd_graph.graphs.base import ICDGraph


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


@dataclass
class CID10Graph(ICDGraph):
    """Class for representing the Brazilian ICD-10 from 2025 version as a graph.

    Files for download:
    http://plataforma.saude.gov.br/cc-br-fic/
    https://buscalai.cgu.gov.br/PedidosLai/DetalhePedido?id=9499386
    """

    year: int = 2025
    version_name: str = "cid-10-bra"
    _chapters_filename: str = "Anexo0050230380.xlsx"
    _block_filename: str = "Anexo 0050230367.xlsx"
    _codes_filename: str = "Anexo0050219792.xlsx"
    _block_internal_code: dict = None

    def add_chapters(self):
        chapters_file = Path(self.files_dir) / self._chapters_filename
        chapters = pl.read_excel(source=chapters_file)
        for line in chapters.iter_rows(named=True):
            start, end = line["Intervalo de códigos"].strip().split("-")
            self.add_or_update_chapter(
                str(line["Nº capitulo"]),
                line["Nome do capítulo"],
                description=line["Nome do capítulo"],
                start=start,
                end=end,
            )

    def add_blocks(self):
        blocks_file = Path(self.files_dir) / self._block_filename
        blocks = pl.read_excel(source=blocks_file)
        self._block_internal_code = {}

        for line in blocks.iter_rows(named=True):
            block_label = line["Intervalo"].strip()
            start, end = block_label.split("-")
            assert self.find_chapter(start) == self.find_chapter(end)
            chapter_code = self.find_chapter(start)
            block_name = self.add_or_update_block(
                start, end, chapter_code, line["Nome agrupamento"].strip()
            )
            block_id = int(line["Nºordem"])
            self._block_internal_code[block_id] = block_label
            self.connect_chapter_block(chapter_code, block_name)

    def add_codes(self):
        codes_file = Path(self.files_dir) / self._codes_filename
        codes = pl.read_excel(source=codes_file)
        last_block_found = None
        number_of_last_block_found_used = 0

        for line in codes.iter_rows(named=True):
            code = line["co_categ_subcateg_sp"].strip()
            title = line["no_categoria_subcategoria"].strip()
            three_char_category = line["co_categoria_pai"]
            try:
                block = self._block_internal_code[
                    int(line["Nº sequencial do agrupamento"])
                ]
                last_block_found = block
            except TypeError:
                # cover cases where "Nº sequencial do agrupamento" is None
                # for this reason, we use the last block found as a fallback
                block = last_block_found
                number_of_last_block_found_used += 1
            chapter = line["Nº do Capitulo"]
            self.add_or_update_code(
                code,
                chapter,
                block,
                three_char_category,
                title=title,
            )

            if len(code) == 3:  # three-character category = first level for codes
                self.connect_block_three_char_category(block, code)
            else:
                self.connect_codes_recursively(code)

        logging.warning(
            f"Used {number_of_last_block_found_used} of the last block found"
        )
