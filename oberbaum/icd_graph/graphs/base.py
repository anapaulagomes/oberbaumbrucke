from abc import ABC
from collections import Counter
from dataclasses import dataclass, field

import networkx as nx
from rich.console import Console
from rich.text import Text
from rich.tree import Tree

ROMAN_NUMERALS = {
    "1": "I",
    "2": "II",
    "3": "III",
    "4": "IV",
    "5": "V",
    "6": "VI",
    "7": "VII",
    "8": "VIII",
    "9": "IX",
    "10": "X",
    "11": "XI",
    "12": "XII",
    "13": "XIII",
    "14": "XIV",
    "15": "XV",
    "16": "XVI",
    "17": "XVII",
    "18": "XVIII",
    "19": "XIX",
    "20": "XX",
    "21": "XXI",
    "22": "XXII",
}


@dataclass
class ICDGraph(ABC):
    """Class for representing the ICD structure as a graph."""

    version_name: str
    year: int
    files_dir: str = field(default_factory=str)
    gml_filepath: str = field(default_factory=str)
    _graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    _root_node: str = "root"
    _chapters: dict = field(default_factory=dict)
    _blocks: dict = field(default_factory=dict)
    _levels: dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the graph and add nodes and edges."""
        self._graph_ready = False
        if self.gml_filepath:
            self._graph = nx.read_gml(self.gml_filepath)

            # load cache
            for node, data in self._graph.nodes(data=True):
                if data.get("type") == "chapter":
                    self._chapters[node] = data
                elif data.get("type") == "block":
                    self._blocks[node] = data

            self._graph_ready = True
            return
        self.add_root_node()
        self.load_initial_data()
        self.add_chapters()
        self.add_blocks()
        self.add_codes()
        self._graph_ready = True

    def add_chapters(self):
        """Add chapters to the graph.

        The chapters should be added using the method `add_chapter`."""
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_codes(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_blocks(self):
        raise NotImplementedError("Version Graph class must implement this method.")

    def add_root_node(self):
        self._graph.add_node(self._root_node)

    def add_or_update_chapter(
        self,
        chapter_code: str,
        chapter_name=None,
        start=None,
        end=None,
        description=None,
    ):
        chapter_code = chapter_code.lstrip("0")  # remove leading zero e.g. "01" -> "1"
        data = {
            "start": start,  # blocks start
            "end": end,  # blocks end
            "name": chapter_code,
            "title": chapter_name,
            "description": description,
        }
        if self._chapters.get(chapter_code):
            # update chapter's data
            updated_data = {
                key: value for key, value in data.items() if value is not None
            }
            self._graph.nodes[chapter_code].update(updated_data)
            return chapter_code

        data["type"] = "chapter"
        self._graph.add_node(chapter_code, **data)
        del data["type"]
        self._chapters[chapter_code] = data
        self.add_edge(self._root_node, chapter_code)
        return chapter_code

    def add_or_update_block(
        self, start=None, end=None, chapter_code=None, title=None, block_name=None
    ):
        """Add blocks to the graph.

        If the chapter code is provided, it will be used to create the edge between chapter and block."""
        block_name = block_name or self.block_name(start, end)
        description = self.block_description(block_name, title)
        data = {
            "start": start,
            "end": end,
            "chapter_code": chapter_code,
            "name": block_name,
            "title": title,
            "description": description,
        }

        if self._blocks.get(block_name):
            # update block's data
            updated_data = {
                key: value for key, value in data.items() if value is not None
            }
            self._graph.nodes[block_name].update(updated_data)
            return block_name

        if not all([start, end]):
            raise Exception("Cannot create block without start and end codes")

        data["type"] = "block"
        self._graph.add_node(block_name, **data)
        del data["type"]
        self._blocks[block_name] = data

        return block_name

    def add_or_update_code(
        self,
        code,
        chapter=None,
        block=None,
        three_char_category=None,
        description=None,
        title=None,
        **kwargs,
    ):
        data = {
            "chapter": chapter,
            "block": block,
            "three_char_category": three_char_category,
            "description": description,
            "name": code,
            "title": title,
            "type": "code",
            "category": len(code),  # FIXME rename to char_len
            # TODO create new attribute called category: category, subcategory, code
        }

        updated_data = {key: value for key, value in data.items() if value is not None}
        if self._graph.nodes.get(code):
            self._graph.nodes[code].update(updated_data)
        else:
            self._graph.add_node(code, **data, **kwargs)
        return code

    def find_parent_block(self, block):
        """Find the parent of a given block.

        A block may be a child of a chapter or another block."""
        block_data = self.get(block)
        block_start_letter = block_data["start"][0]
        block_end_letter = block_data["end"][0]
        for current_block, current_data in self.blocks(data=True):
            if (
                current_data["start"][0] == block_start_letter
                and current_data["end"][0] == block_end_letter
            ):
                match_start = int(block_data["start"][1:]) >= int(
                    current_data["start"][1:]
                )
                match_end = int(current_data["end"][1:]) >= int(block_data["end"][1:])

                if block != current_block and (match_start and match_end):
                    return current_block
        return

    def get(self, node):
        """Get the data for a given element in the graph."""
        return self._graph.nodes.get(node)

    def is_connected(self, node1, node2):
        """Check if two nodes are connected in the graph."""
        return self._graph.has_edge(node1, node2) or self._graph.has_edge(node2, node1)

    def connect_blocks_sub_blocks(
        self, block_name, sub_block_name=None, chapter_code=None
    ):
        """Create the edge between block and sub-block.

        Not all blocks have sub-blocks, so this method is optional. And even if they have it,
        sometimes they are not explicitly connected in the file.
        """
        if block_name and sub_block_name:
            self.connect_blocks(block_name, sub_block_name)
        elif block_name and not sub_block_name:
            # we assume that the block is missing its parent
            parent_block = self.find_parent_block(block_name)
            if parent_block:
                self.connect_blocks(parent_block, block_name)  # block and sub-block
                if chapter_code:
                    # given that the block is missing its parent, we need to connect the chapter with the block
                    self.connect_chapter_block(chapter_code, parent_block)
                return parent_block, block_name
        return block_name, sub_block_name

    def connect_block_three_char_category(self, block, three_char_category):
        """Create the edge between chapter and block."""
        self.add_edge(block, three_char_category)

    def connect_chapter_block(self, chapter_code, block_name):
        """Create the edge between chapter and block.

        If the chapter code is not present in the block, it will be added to the block node
        for convenience."""
        block_name = self.add_or_update_block(
            block_name=block_name, chapter_code=chapter_code
        )
        chapter_code = self.add_or_update_chapter(chapter_code)
        self.add_edge(chapter_code, block_name)

    def connect_blocks(self, block, sub_block):
        """Create the edge between block and sub-block."""
        self.add_edge(block, sub_block)

    def chapters(self, roman_numerals=False, data=False):
        if data:
            return self._chapters.items()
        codes = list(self._chapters.keys())
        if roman_numerals:
            return [ROMAN_NUMERALS[code] for code in codes]
        return codes

    def categories(self, from_block=None):
        """Get all categories in the graph."""
        all_categories = set()
        for block in self.blocks():
            if from_block and block != from_block:
                continue
            all_categories.update(nx.descendants(self._graph, block))
        return all_categories

    def is_code(self, code):
        """Codes might have between 3-7 chars and should be at the final level of subdivision."""
        if code in self.blocks() or code in self.chapters():
            return False
        if len(code) < 3 or len(code) > 7:
            return False
        do_not_point_to_other_nodes = self._graph.out_degree(code) == 0
        receive_nodes = self._graph.in_degree(code) == 1
        return receive_nodes and do_not_point_to_other_nodes

    def get_codes(self, data=False):
        """
        # TODO
        # categories = 3 character codes; a 3 char code that has no following codes is equivalent to a code
        # subcategories = are either 4 or 5 character code
        # codes = codes may be 3-7 chars (final level of subdivision/hierarchy)
        """
        for node, node_data in self._graph.nodes(data=True):
            if self.is_code(node):
                if data:
                    yield node, node_data
                else:
                    yield node

    def codes(self, from_chapter=None, exclude_3_char=True):
        all_codes = set()
        for chapter in self.chapters():
            if from_chapter is None:  # all codes
                all_codes.update(nx.descendants(self._graph, chapter))
                continue

            if chapter == from_chapter:  # specific chapter
                all_codes.update(nx.descendants(self._graph, chapter))
                break

        # remove blocks and chapters
        if exclude_3_char:
            all_codes = {
                node
                for node in all_codes
                if self._graph.out_degree(node) == 0
                and self._graph.in_degree(node) == 1  # leaf
            }
        return all_codes

    def levels(self):
        levels = []
        for node, data in self._graph.nodes(data=True):
            if data.get("category"):
                levels.append(data["category"])
            elif data.get("type") == "block":  # FIXME rename to type
                levels.append(2)
            elif data.get("type") == "chapter":  # FIXME rename to type
                levels.append(1)
        counter = Counter(levels)
        return dict(sorted(counter.items()))

    def codes_per_level(self):
        # FIXME misleading, since blocks and sub-blocks may vary and create different levels
        if self._graph_ready and not self._levels:
            layers = list(nx.bfs_layers(self._graph, self._root_node))
            self._levels = {
                level: layer for level, layer in enumerate(layers) if level != 0
            }
            return self._levels
        return self._levels

    def blocks(self, data=False):
        """Get all blocks in the graph."""
        if data:
            return self._blocks.items()
        return list(self._blocks.keys())

    @staticmethod
    def block_name(start, end):
        """Get the block name for a given start and end code."""
        return f"{start}-{end}"

    @staticmethod
    def block_description(node, title):
        """Get the block description for a given start and end code.

        Example: Intestinal infectious diseases (A00-A09)
        """
        if title:
            return f"{title} ({node})"
        else:
            return node

    def three_char_codes(self):
        # FIXME misleading, since blocks and sub-blocks may vary and create different levels
        return self.codes_per_level()[3]

    def four_char_codes(self):
        # FIXME misleading, since blocks and sub-blocks may vary and create different levels
        return self.codes_per_level()[4]

    def export(self):
        gml_file = f"{self.version_name}.gml"
        root_node = self._root_node
        graph_copy = self._graph.copy()
        graph_copy = from_none_to_empty(
            graph_copy, root_node, graph_copy.nodes(data=True)
        )
        nx.write_gml(graph_copy, gml_file)
        return gml_file

    def predecessors(self, node, _track=None):
        if _track is None:
            _track = []
        result = nx.predecessor(self._graph, self._root_node, node)
        _track.extend(result)

        if not result:
            if self._root_node in _track:
                _track.remove(self._root_node)
            return _track
        return self.predecessors(result[0], _track)

    def find_chapter(self, code):
        """Find the chapter for a given code.

        Every chapter has a start and end category code.
        Use this method to find the chapter for a given code."""
        return self._find_in(self.chapters(data=True), code)

    def find_block(self, code, include_subblocks=False):
        """Find the block for a given code.

        Every block has a start and end category code.
        Use this method to find the block for a given code."""
        return self._find_in(self.blocks(data=True), code, include_subblocks)

    def _find_in(self, data_set: dict, code: str, return_all=False):
        letter = code[0]
        found = []
        for item, data in data_set:
            start = data.get("start")
            end = data.get("end")
            if not start and not end:
                continue

            number = int(code[1:3])
            start_number = int(start[1:])
            end_number = int(end[1:])
            start_letter = start[0]
            end_letter = end[0]

            if letter == start_letter == end_letter:
                if start_number <= number <= end_number:
                    if not return_all:
                        return item

                    found.append(item)
            else:
                if letter == start_letter:
                    if number >= start_number:
                        if not return_all:
                            return item

                        found.append(item)
                elif letter == end_letter:
                    if number <= end_number:
                        if not return_all:
                            return item

                        found.append(item)
                else:
                    if start_letter < letter < end_letter:
                        if not return_all:
                            return item

                        found.append(item)

        if not return_all:
            return None

        return found

    def connect_codes_recursively(self, current_code):
        """Connect the code with its upper levels code, if they exist."""
        previous_code = current_code[0 : len(current_code) - 1]
        if len(previous_code) >= 3:
            current_code = self.add_or_update_code(current_code)
            previous_code = self.add_or_update_code(previous_code)
            self.add_edge(previous_code, current_code)
            return self.connect_codes_recursively(previous_code)
        return current_code

    def connect_codes(self, code1, code2):
        """Connect two codes in the graph."""
        code1 = self.add_or_update_code(code1)
        code2 = self.add_or_update_code(code2)
        if code1 == code2:
            return
        self.add_edge(code1, code2)

    def add_edge(self, node1, node2):
        """Add an edge between two nodes in the graph."""
        if node1 == node2:
            return
        self._graph.add_edge(node1, node2)

    def load_initial_data(self):
        """Load initial data for the next steps of the graph creation."""
        pass


def print_graph(graph, root_node=None):
    """
    Print an ICDGraph in the terminal.

    Args:
        graph: A ICDGraph that is a tree
        root_node: The root node to start from (if None, will try to find a root)
    """
    console = Console()
    root_node = root_node or graph._root_node
    rich_tree = Tree(Text(str(root_node), style="bold"))
    G = graph._graph

    def add_children(parent_node, rich_parent):
        for child in G.successors(parent_node):
            child_text = Text(child)
            child_text.stylize("gray")
            rich_child = rich_parent.add(child_text)
            add_children(child, rich_child)

    add_children(root_node, rich_tree)
    console.print(rich_tree)


def from_none_to_empty(a_graph, root_node, data_dict):
    """Convert all None values to empty strings in a dictionary."""
    for item, data in data_dict:
        for key, value in data.items():
            if value is None:
                data[key] = ""
    return a_graph


def get_subgraph(graph, from_, to_, filename=None, include_children=False):
    if not filename:
        filename = "subgraph.gml"
    if not from_:
        from_ = graph._root_node

    path = nx.shortest_path(graph._graph, from_, to_)
    subgraph = nx.subgraph(graph._graph, path)
    if include_children:
        children = graph._graph.successors(to_)
        subgraph = subgraph.copy()  # unfreeze it
        for child in children:
            data = graph.get(child)
            subgraph.add_node(child, **data)
            subgraph.add_edge(to_, child)

    from_none_to_empty(subgraph, graph._root_node, subgraph.nodes(data=True))
    nx.write_gml(subgraph, filename)
    return subgraph
