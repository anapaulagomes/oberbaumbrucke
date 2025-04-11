import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from oberbaum.icd_graph import WHOICDGraph

app = typer.Typer()
graph_app = typer.Typer()
app.add_typer(graph_app, name="graph")
console = Console()


@graph_app.command()
def create(icd_files_dir: str, export: bool = False):
    graph = WHOICDGraph(files_dir=icd_files_dir)

    tree = Tree(graph.version_name)
    for level, number_of_nodes in graph.levels().items():
        tree.add(f"[green] {level} ({number_of_nodes})")

    table = Table("Name", "Item")
    table.add_row("Chapters", str(graph.chapters()))
    table.add_row("# levels", tree)
    table.add_row("# codes", str(len(graph.codes())))
    console.print(table)


if __name__ == "__main__":
    app()
