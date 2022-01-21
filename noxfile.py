#!/usr/bin/env python3
"""Configuration file for nox."""
import tempfile

import nox
from nox import session as Session

package = "event_horyzen"
nox.options.sessions = "lint", "tests", "mypy", "black", "docs/conf.py"


def install_with_constraints(session, *args, **kwargs):
    """Install using constraints from poetry."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            "--without-hashes",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


# @nox.session(python=["3.10", "3.9", "3.8", "3.7"])
@nox.session(python=["3.10"])
def tests(session):
    """Run tests."""
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "coverage[toml]", "pytest", "pytest-cov")
    session.run("pytest", *args)


locations = "event_horyzen", "tests", "noxfile.py"


@nox.session(python=["3.10"])
def lint(session):
    """Lint code."""
    args = session.posargs or locations
    install_with_constraints(
        session,
        "flake8",
        "flake8-black",
        "flake8-bugbear",
        "flake8-import-order",
        "flake8-docstrings",
        "darglint",
    )
    session.run("flake8", *args)


@nox.session(python=["3.10"])
def mypy(session):
    """Check types."""
    args = session.posargs or locations
    install_with_constraints(session, "mypy")
    session.run("mypy", "--install-types")
    session.run("mypy", *args)


@nox.session(python=["3.10"])
def black(session):
    """Run black formatter."""
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session(python=["3.10"])
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "xdoctest")
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(python=["3.10"])
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", "-E", "pyqt", external=True)
    install_with_constraints(session, "sphinx", "sphinx-autodoc-typehints")
    session.run("sphinx-build", "docs", "docs/_build")
