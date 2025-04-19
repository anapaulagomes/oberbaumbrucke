import typer
from rich.console import Console
from rich.tree import Tree

from oberbaum.icd_graph.graph import get_graph
from oberbaum.icd_graph.match import export_matches, match_codes

app = typer.Typer()
graph_app = typer.Typer()
app.add_typer(graph_app, name="graph")
console = Console()


def summary(a_list):
    n = 10
    if len(a_list) > n:
        return ", ".join(a_list[:n]) + "..."
    return ", ".join(a_list)


@graph_app.command()
def create(version: str, icd_files_dir: str, export: bool = False):
    graph = get_graph(version, icd_files_dir)

    tree = Tree(graph.version_name)
    chapters = graph.chapters(roman_numerals=True)
    blocks = graph.blocks()
    all_codes = list(graph.categories())
    tree.add(f"[gold3] Chapters ({len(chapters)}): [/gold3] {summary(chapters)}")
    tree.add(f"[gold3] Blocks ({len(blocks)}): [/gold3] {summary(blocks)}")
    tree.add(f"[gold3] Codes ({len(all_codes)}) [/gold3] {summary(all_codes)}")
    tree.add(f"All nodes ({len(graph._graph.nodes)})")
    console.print(tree)

    if export:
        export_path = graph.export()
        console.print(f"Graph exported to {export_path}")


@graph_app.command()
def match(
    version: str,
    version_gml_filepath: str,
    other_version: str,
    other_gml_filepath: str,
    output: str = None,
):
    if not output:
        version = version.lower()
        other_version = other_version.lower()
        output = f"{version}___{other_version}.csv"
    graph = get_graph(version, gml_filepath=version_gml_filepath)
    other_graph = get_graph(other_version, gml_filepath=other_gml_filepath)

    matches_summary, matches = match_codes(graph, other_graph)
    export_matches(matches, output)
    console.print(matches_summary)
    console.print(f"Matches exported to {output}")


if __name__ == "__main__":
    app()
