"""Admin commands. Usage: uv run python -m hospital_agent.cli create-platform-admin <username>"""

import asyncio

import typer

from hospital_agent.core.config import get_settings
from hospital_agent.db.session import create_engine, create_session_factory
from hospital_agent.db.unit_of_work import UnitOfWork
from hospital_agent.services.auth_service import AuthService, UsernameTakenError

app = typer.Typer(no_args_is_help=True)


@app.command()
def create_platform_admin(
    username: str,
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
) -> None:
    """Create the platform admin account (there is no public sign-up for this role)."""

    async def run() -> None:
        settings = get_settings()
        engine = create_engine(settings)
        try:
            async with create_session_factory(engine)() as session:
                await AuthService(UnitOfWork(session), settings).create_platform_admin(
                    username, password
                )
        finally:
            await engine.dispose()

    try:
        asyncio.run(run())
    except UsernameTakenError:
        typer.echo(f"User '{username}' already exists.", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Platform admin '{username}' created.")


@app.command()
def version() -> None:
    """Print the app version."""
    typer.echo("hospital-agent 0.1.0")


if __name__ == "__main__":
    app()
