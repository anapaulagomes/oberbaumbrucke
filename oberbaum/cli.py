import os

import networkx as nx
import typer
from rich.console import Console
from rich.tree import Tree

from oberbaum.config import get_results_dir
from oberbaum.icd_graph.embeddings import (
    create_embeddings_table_if_not_exists,
    create_matching_table_if_not_exists,
    get_connection,
    store_embeddings,
)
from oberbaum.icd_graph.experiments import from_logs_to_df
from oberbaum.icd_graph.graph_overlap import compare_graphs
from oberbaum.icd_graph.graphs.base import get_subgraph
from oberbaum.icd_graph.graphs.brazil import CID10Graph
from oberbaum.icd_graph.graphs.germany import ICD10GMGraph
from oberbaum.icd_graph.graphs.usa import ICD10CMGraph
from oberbaum.icd_graph.graphs.who import WHOICDGraph
from oberbaum.icd_graph.match import export_matches, match_codes
from oberbaum.icd_graph.models import MODELS

app = typer.Typer()
graph_app = typer.Typer()
db_app = typer.Typer()
app.add_typer(graph_app, name="graph")
app.add_typer(db_app, name="db")
console = Console()


def get_graph(version_name: str, files_dir: str = None, gml_filepath: str = None):
    versions = {
        "icd-10-who": WHOICDGraph,
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
        "cid-10-bra",
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
    results_dir: str = None,
    chosen_model: str = None,
    threshold: float = 0.7,
):
    console.print("[bold green]Loading graphs...[/bold green]")
    graph = get_graph(version, gml_filepath=version_gml_filepath)
    other_graph = get_graph(other_version, gml_filepath=other_gml_filepath)
    results_dir = results_dir or get_results_dir(subfolder="artifacts")

    for model in MODELS:
        if not (chosen_model is None or (chosen_model and model == chosen_model)):
            continue
        if not output:
            version = version.lower()
            other_version = other_version.lower()
            model_name = model.name.split("/")[-1]
            output = f"{results_dir}/{version}___{other_version}__{model_name}_{threshold}.csv"

        console.print(
            f"[bold green]Using model: {model.name} with threshold: {threshold}[/bold green]"
        )
        matches_summary, matches = match_codes(
            graph, other_graph, model.name, threshold=threshold
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


def _match_all(**kwargs):
    threshold = kwargs.get("threshold", 0.7)
    console.print("Fetching all models...")
    who_graph = get_graph("icd-10-who", gml_filepath="icd-10-who.gml")
    results_dir = get_results_dir(subfolder="artifacts")
    for model in MODELS:
        console.print(
            f"[bold green]Using model: {model.name} with threshold: {threshold}[/bold green]"
        )
        for graph in all_graphs():
            model_name = model.name.split("/")[-1]
            output = f"{results_dir}/{graph.version_name}___{who_graph.version_name}__{model_name}_{threshold}.csv"

            matches_summary, matches = match_codes(
                graph, who_graph, model.name, threshold=threshold
            )
            export_matches(matches, output)

            console.print("\n[bold yellow]Match Summary:[/bold yellow]")
            for key, value in matches_summary.items():
                console.print(f"  {key}: {value}")

            console.print(f"\n[bold green]Matches exported to {output}[/bold green]")


def _graphs_overlap(**kwargs):
    print(kwargs)
    graphs = all_graphs()
    who_graph = next(graphs)
    assert who_graph.version_name == "icd-10-who"

    if kwargs.get("all_graphs", False):
        for graph in graphs:
            compare_graphs(graph, who_graph, kwargs["method"], kwargs["chapter"])
    else:
        graph_name = kwargs["graph_version_name"]
        graph = get_graph(graph_name, gml_filepath=f"{graph_name}.gml")
        compare_graphs(graph, who_graph, kwargs["method"], kwargs["chapter"])


@graph_app.command("experiments")
def run_experiments(
    name,
    graph_version_name: str = None,
    all_graphs: bool = False,
    threshold: float = 0.7,
    only_codes: bool = False,
    method: str = "mcosi",
    chapter: int = None,
):
    kwargs = {
        "threshold": threshold,
        "only_codes": only_codes,
        "method": method,
        "chapter": chapter,
        "all_graphs": all_graphs,
        "graph_version_name": graph_version_name,
    }
    experiments_available = {
        "match_all": _match_all,
        "graphs_overlap": _graphs_overlap,
    }
    experiments_available.get(name)(**kwargs)


@db_app.command("create")
def configure_db(db_name: str = None):
    db_name = db_name or os.getenv("EMBEDDINGS_DB")
    con = get_connection(writeable=True, db_name=db_name)
    create_matching_table_if_not_exists(con)
    create_embeddings_table_if_not_exists(con)
    console.print(f"\n[bold green]DB {db_name} successfully created.[/bold green]")


@graph_app.command("parse-logs")
def parse_logs(
    logs_dir: str,
    output_file: str = None,
):
    """Parse logs and save to a CSV file."""
    if not output_file:
        results_dir = get_results_dir()
        output_file = f"{results_dir}/results.csv"

    df = from_logs_to_df(logs_dir)
    df.write_csv(output_file)
    console.print(f"[bold green]Parsed logs and saved to {output_file}[/bold green]")


if __name__ == "__main__":
    app()
