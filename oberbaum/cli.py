import networkx as nx
import typer
from rich.console import Console
from rich.tree import Tree

from oberbaum.icd_graph.embeddings import store_embeddings
from oberbaum.icd_graph.graph_overlap import compare_graphs
from oberbaum.icd_graph.graphs.base import get_subgraph
from oberbaum.icd_graph.graphs.brazil import CID10Graph, CID10Graph2008
from oberbaum.icd_graph.graphs.germany import ICD10GMGraph
from oberbaum.icd_graph.graphs.usa import ICD10CMGraph
from oberbaum.icd_graph.graphs.who import WHOICDGraph
from oberbaum.icd_graph.match import export_matches, match_codes
from oberbaum.icd_graph.models import MODELS

app = typer.Typer()
graph_app = typer.Typer()
app.add_typer(graph_app, name="graph")
console = Console()


def get_graph(version_name: str, files_dir: str = None, gml_filepath: str = None):
    versions = {
        "icd-10-who": WHOICDGraph,
        "cid-10-bra-2008": CID10Graph2008,
        "cid-10-bra": CID10Graph,
        "icd-10-gm": ICD10GMGraph,
        "icd-10-cm": ICD10CMGraph,
    }
    return versions[version_name](files_dir=files_dir, gml_filepath=gml_filepath)


def all_graphs():
    graphs = [
        "icd-10-who",
        "icd-10-gm",
        "icd-10-cm",
        "cid-10-bra-2008",
    ]
    for graph in graphs:
        yield get_graph(graph, gml_filepath=f"{graph}.gml")


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


@graph_app.command()
def subgraph(
    version: str,
    icd_files_dir: str,
    target: str,
    source: str = None,
    include_children: bool = False,
):
    graph = get_graph(version, icd_files_dir)
    filename = f"subgraph-{graph.version_name}-{target}{'-include-children' if include_children else ''}.gml"
    try:
        subgraph = get_subgraph(graph, source, target, filename, include_children)
        console.print(
            f"Exported to: {filename}."
            f"There are {len(subgraph.nodes)} nodes (original graph has {len(graph._graph.nodes)})"
        )
    except nx.NodeNotFound:
        console.print(f"Node {target} not found in the graph {graph.version_name}")


@graph_app.command()
def embeddings(
    version: str = None,
    icd_files_dir: str = None,
    version_gml_filepath: str = None,
    force: bool = False,
):
    if all([version, icd_files_dir, version_gml_filepath]):
        console.print(f"Fetching graph {version}...")
        graph = get_graph(version, icd_files_dir, version_gml_filepath)
        console.print("Storing embeddings...")
        store_embeddings(graph, force)
    else:
        console.print("Fetching all graphs...")
        for graph in all_graphs():
            console.print(f"Storing embeddings for graph {graph.version_name}...")
            store_embeddings(graph, force)


def _match_all(threshold):
    console.print("Fetching all models...")
    who_graph = get_graph("icd-10-who", gml_filepath="icd-10-who.gml")
    for model in MODELS:
        console.print(
            f"[bold green]Using model: {model.name} with threshold: {threshold}[/bold green]"
        )
        for graph in all_graphs():
            model_name = model.name.split("/")[-1]
            output = f"artifacts/{graph.version_name}___{who_graph.version_name}__{model_name}_{threshold}.csv"

            matches_summary, matches = match_codes(
                graph, who_graph, model.name, threshold=threshold
            )
            export_matches(matches, output)

            console.print("\n[bold yellow]Match Summary:[/bold yellow]")
            for key, value in matches_summary.items():
                console.print(f"  {key}: {value}")

            console.print(f"\n[bold green]Matches exported to {output}[/bold green]")


def _graphs_overlap(**kwargs):
    graphs = all_graphs()
    who_graph = next(graphs)
    assert who_graph.version_name == "icd-10-who"

    for graph in graphs:
        compare_graphs(graph, who_graph, kwargs["only_codes"])


@graph_app.command("experiments")
def run_experiments(name, threshold: float = 0.7, only_codes: bool = False):
    kwargs = {"threshold": threshold, "only_codes": only_codes}
    experiments_available = {
        "match_all": _match_all,
        "graphs_overlap": _graphs_overlap,
    }
    experiments_available.get(name)(**kwargs)


if __name__ == "__main__":
    app()
