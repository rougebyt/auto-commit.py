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

    message = generate_smart_message(repo)
    if message["subject"] == "No changes detected":
        console.print("[yellow]No changes to commit.[/yellow]")
        return

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
        # Stage everything (including untracked)
        repo.git.add(A=True)

        # ----> NEW: proper GitPython commit <----
        if amend:
            # Amend the last commit (keeps the same author/date)
            repo.index.commit(full_msg, head=True, amend=True)
            action = "amended"
        else:
            repo.index.commit(full_msg)
            action = "committed"
        # -----------------------------------------

        console.print(f"[bold green]Successfully {action}![/bold green]")
    except Exception as e:
        console.print(f"[red]Commit failed: {e}[/red]")