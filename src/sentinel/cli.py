"""Command-line entrypoint."""
from __future__ import annotations

import logging
import os

import click

from sentinel.mimo_client import MiMoClient
from sentinel.orchestrator import SweepConfig, run_continuous, run_once


@click.command()
@click.option("--target", required=True, help="OpenAPI spec URL.")
@click.option("--base-url", required=True, help="Base URL of API to scan.")
@click.option("--mode", default="once",
              type=click.Choice(["once", "continuous"]))
@click.option("--max-endpoints", default=100, type=int)
@click.option("--interval", default=3600, type=int,
              help="Seconds between sweeps in continuous mode.")
def main(target: str, base_url: str, mode: str,
         max_endpoints: int, interval: int) -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    cfg = SweepConfig(
        target_openapi_url=target,
        base_url=base_url,
        sweep_interval_sec=interval,
        max_endpoints=max_endpoints,
    )
    mimo = MiMoClient()
    try:
        if mode == "continuous":
            run_continuous(cfg, mimo)
        else:
            result = run_once(cfg, mimo)
            click.echo(result)
    finally:
        mimo.close()


if __name__ == "__main__":
    main()
