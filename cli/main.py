"""DevEx CLI — command-line interface for the agent platform."""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from sdk.client import DevExAgent

app = typer.Typer(help="DevEx Agent Platform — AI-powered developer tool recommendations")
console = Console()


def get_agent(session: str) -> DevExAgent:
    return DevExAgent(session_id=session)


@app.command()
def recommend(
    query: str = typer.Argument(..., help="Natural language query, e.g. 'best testing lib for FastAPI'"),
    stack: str = typer.Option("", "--stack", "-s", help="Comma-separated stack, e.g. 'FastAPI,Redis,PostgreSQL'"),
    constraints: str = typer.Option("", "--constraints", "-c", help="Comma-separated constraints"),
    session: str = typer.Option("default", "--session", help="Session ID for memory continuity"),
):
    """Get an AI-powered tool recommendation."""
    agent = get_agent(session)
    stack_list = [s.strip() for s in stack.split(",") if s.strip()]
    constraint_list = [c.strip() for c in constraints.split(",") if c.strip()]

    with console.status("[bold green]Agents thinking...[/bold green]"):
        result = agent.recommend(query, stack=stack_list, constraints=constraint_list)

    # Top recommendation panel
    console.print(Panel(
        f"[bold cyan]{result.recommendation}[/bold cyan]\n\n"
        f"[white]{result.reasoning}[/white]\n\n"
        f"[yellow]⚠ Tradeoffs:[/yellow] {result.tradeoffs}\n\n"
        f"[green]▶ Getting started:[/green] {result.getting_started}",
        title=f"[bold green]✓ Recommendation[/bold green]  [dim](confidence: {result.confidence}%)[/dim]",
        border_style="green",
        padding=(1, 2),
    ))

    # Alternatives table
    if result.alternatives:
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("Alternative")
        table.add_column("When to choose instead")
        for alt in result.alternatives:
            table.add_row(f"#{alt['rank']}", alt['name'], alt['when_to_choose'])
        console.print(table)

    if result.avoid:
        console.print(f"[red]✗ Avoid:[/red] {result.avoid}\n")

    console.print(f"[dim]Latency: {result.latency_ms:.0f}ms · Session: {result.session_id}[/dim]")


@app.command()
def history(
    session: str = typer.Option("default", "--session", help="Session ID"),
    last: int = typer.Option(10, "--last", "-n", help="Number of recent turns to show"),
):
    """Show recommendation history for a session."""
    agent = get_agent(session)
    turns = agent.history()[-last:]
    if not turns:
        console.print("[dim]No history for this session.[/dim]")
        return
    table = Table(title=f"Session: {session}", box=box.SIMPLE)
    table.add_column("#", style="dim")
    table.add_column("Query")
    table.add_column("Recommended")
    table.add_column("Confidence")
    for i, turn in enumerate(turns):
        table.add_row(str(i+1), turn.get("query",""), turn.get("recommendation",""), f"{turn.get('confidence','')}%")
    console.print(table)


@app.command()
def recall(
    query: str = typer.Argument(..., help="Search past team decisions"),
    session: str = typer.Option("default", "--session"),
):
    """Search long-term semantic memory for past team decisions."""
    agent = get_agent(session)
    result = agent.recall(query)
    console.print(Panel(result or "[dim]No relevant past decisions found.[/dim]",
                        title="[bold]Team Memory[/bold]", border_style="blue"))


if __name__ == "__main__":
    app()
