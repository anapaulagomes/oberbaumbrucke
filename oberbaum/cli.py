import typer
from rich.console import Console
from rich.tree import Tree

from oberbaum.icd_graph.graphs.brazil import CID10Graph
from oberbaum.icd_graph.graphs.germany import ICD10GMGraph
from oberbaum.icd_graph.graphs.usa import ICD10CMGraph
from oberbaum.icd_graph.graphs.who import WHOICDGraph
from oberbaum.icd_graph.match import export_matches, match_codes

app = typer.Typer()
graph_app = typer.Typer()
app.add_typer(graph_app, name="graph")
console = Console()


def get_graph(version_name: str, files_dir: str = None, gml_filepath: str = None):
    versions = {
        "icd-10-who": WHOICDGraph,
        "cid-10-bra": CID10Graph,
        "icd-10-gm": ICD10GMGraph,
        "icd-10-cm": ICD10CMGraph,
    }
    return versions[version_name](files_dir=files_dir, gml_filepath=gml_filepath)


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
    model: str = "BAAI/bge-m3",
    threshold: float = 0.7,
):
    if not output:
        version = version.lower()
        other_version = other_version.lower()
        model_name = model.split("/")[-1]
        output = f"artifacts/{version}___{other_version}__{model_name}_{threshold}.csv"

    console.print("[bold green]Loading graphs...[/bold green]")
    graph = get_graph(version, gml_filepath=version_gml_filepath)
    other_graph = get_graph(other_version, gml_filepath=other_gml_filepath)

    console.print(
        f"[bold green]Using model: {model} with threshold: {threshold}[/bold green]"
    )
    matches_summary, matches = match_codes(
        graph, other_graph, model, threshold=threshold
    )

    export_matches(matches, output)

    console.print("\n[bold yellow]Match Summary:[/bold yellow]")
    for key, value in matches_summary.items():
        console.print(f"  {key}: {value}")

    console.print(f"\n[bold green]Matches exported to {output}[/bold green]")


if __name__ == "__main__":
    app()
