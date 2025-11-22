from dataclasses import dataclass
from pathlib import Path

from oberbaum.graphs.base import ICDGraph


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
            self.add_or_update_chapter(chapter_code, chapter_name)

    def add_blocks(self):
        blocks_file = Path(self.files_dir) / self._block_filename
        previous_chapter = None
        previous_end = None
        chapters_start_end = {}
        for line in blocks_file.read_text().splitlines():
            start, end, chapter_code, title = line.split(";")
            chapter_code = self.normalize_chapter_code(chapter_code)
            block_name = self.add_or_update_block(start, end, chapter_code, title)
            self.connect_chapter_block(chapter_code, block_name)

            if not chapters_start_end.get(
                chapter_code
            ):  # first time this chapter appears
                chapters_start_end[chapter_code] = {"start": start}

            if previous_chapter != chapter_code:
                if previous_chapter:
                    chapters_start_end[previous_chapter]["end"] = previous_end
                previous_chapter = chapter_code

            previous_end = end

        chapters_start_end[previous_chapter]["end"] = previous_end
        for chapter, start_end in chapters_start_end.items():
            self.add_or_update_chapter(
                chapter, start=start_end["start"], end=start_end["end"]
            )

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

            if len(code) == 3:
                title = fields[9]
            elif len(code) == 4:
                title = fields[10]
            else:
                title = fields[8]

            extra_data = {"formatted_code": fields[5]}

            self.add_or_update_code(
                code,
                chapter=chapter,
                block=block,
                three_char_category=three_char_category,
                title=title,
                **extra_data,
            )

            if fields[0] == "3":  # from the column hierarchy_level
                self.connect_block_three_char_category(block, code)
            else:
                self.connect_codes_recursively(code)
