# auto_commit/cli.py
import click
from rich.console import Console
from rich.panel import Panel
from git import Repo, InvalidGitRepositoryError
from .analyzer import generate_smart_message
from ._version import __version__  # ← Import from _version.py

console = Console()


@click.command()
@click.version_option(__version__, "--version", "-v")
@click.option("--dry-run", is_flag=True, help="Show message without committing")
@click.option("--amend", is_flag=True, help="Amend last commit")
def main(dry_run: bool, amend: bool):
    """Smart git commit with AI-style messages"""
    try:
        repo = Repo(search_parent_directories=True)
    except InvalidGitRepositoryError:
        console.print("[red]Not a git repository![/red]")
        raise click.Abort()

    if repo.bare:
        console.print("[red]Bare repo detected![/red]")
        raise click.Abort()

    if not repo.index.diff(None) and not repo.untracked_files:
        console.print("[yellow]No changes to commit.[/yellow]")
        return

    message = generate_smart_message(repo)
    full_msg = f"{message['type']}({message['scope']}): {message['subject']}\n\n{message['body']}"

    console.print(
        Panel(
            f"[bold cyan]Suggested Commit[/bold cyan]\n\n{full_msg}",
            title=f"auto-commit.py v{__version__}",
            border_style="blue",
        )
    )

    if dry_run:
        console.print("[green]Dry run complete.[/green]")
        return

    if not click.confirm("Commit this message?", default=True):
        console.print("[yellow]Commit aborted.[/yellow]")
        return

    try:
        repo.git.add(A=True)
        commit_cmd = ["commit"]
        if amend:
            commit_cmd.append("--amend")
        commit_cmd.extend(["-m", full_msg])
        repo.git.execute(commit_cmd)
        action = "amended" if amend else "committed"
        console.print(f"[bold green]Successfully {action}![/bold green]")
    except Exception as e:
        console.print(f"[red]Commit failed: {e}[/red]")
