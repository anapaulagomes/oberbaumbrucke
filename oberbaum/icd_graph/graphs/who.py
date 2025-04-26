from dataclasses import dataclass
from pathlib import Path

from oberbaum.icd_graph.graphs.base import ICDGraph


@dataclass
class WHOICDGraph(ICDGraph):
    """Class for representing the WHO ICD structure as a graph.

    The version implemented here is the 2019.
    Files for download: https://icdcdn.who.int/icd10/meta/icd102019enMeta.zip
    ICD-10 metadata Format: https://icdcdn.who.int/icd10/metainfo.html
    Guidelines: https://icd.who.int/browse10/Content/statichtml/ICD10Volume2_en_2019.pdf
    """

    year: int = 2019
    version_name: str = "icd-10-who"
    _chapters_filename: str = "icd102019syst_chapters.txt"
    _block_filename: str = "icd102019syst_groups.txt"
    _codes_filename: str = "icd102019syst_codes.txt"

    def add_chapters(self):
        """The instructions mention 21 chapters but the file has 22."""
        chapters_file = Path(self.files_dir) / self._chapters_filename
        for line in chapters_file.read_text().splitlines():
            chapter_code, chapter_name = line.split(";", 1)
            self.add_or_update_chapter(
                chapter_code, chapter_name, description=chapter_name
            )

    def add_blocks(self):
        blocks_file = Path(self.files_dir) / self._block_filename
        for line in blocks_file.read_text().splitlines():
            start, end, chapter_code, title = line.split(";")
            block_name = self.add_or_update_block(start, end, chapter_code, title)
            self.connect_chapter_block(chapter_code, block_name)

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
        codes_file = Path(self.files_dir) / self._codes_filename
        for line in codes_file.read_text().splitlines():
            fields = line.split(";")
            code = fields[7]  # 3, 4 or 5 char category
            three_char_category = code[:3]
            block = self.find_block(three_char_category)
            chapter = fields[3]
            description = fields[8]
            title = fields[9]
            extra_data = {"subtitle": fields[10], "formatted_code": fields[5]}

            self.add_or_update_code(
                code,
                chapter,
                block,
                three_char_category,
                description,
                title,
                **extra_data,
            )

            if fields[0] == "3":
                self.connect_block_three_char_category(block, code)
            else:
                self.connect_codes_recursively(code)
