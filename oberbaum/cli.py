import typer
from rich.console import Console
from rich.tree import Tree

from oberbaum.icd_graph import get_graph

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
    levels = graph.levels()
    tree.add(
        f"[gold3] 1. Chapters ({levels[1]}): [/gold3] {summary(graph.chapters(roman_numerals=True))}"
    )
    tree.add(f"[gold3] 2. Blocks ({levels[2]}): [/gold3] {summary(graph.blocks())}")
    tree.add(
        f"[gold3] 3. Three-character categories ({levels[3]}): [/gold3] {summary(graph.three_char_codes())}"
    )
    tree.add(
        f"[gold3] 4. Four-character categories ({levels[4]}): [/gold3] {summary(graph.four_char_codes())}"
    )
    console.print(tree)
    console.print(f"\nNr. of codes: {len(graph.categories())}")

    if export:
        export_path = graph.export()
        console.print(f"Graph exported to {export_path}")


if __name__ == "__main__":
    app()
