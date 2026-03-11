import json
import sys
from typing import Optional

import typer

from jspprint.io import filter_by_key, print_csv, print_json, read_csv, read_json, update_json

app = typer.Typer()


@app.command()
def main(
    file: Optional[str] = typer.Argument(
        None, help="Path to a JSON or CSV file. Reads from stdin if omitted (JSON only)."
    ),
    key: Optional[str] = typer.Argument(
        None, help="Key to filter by, using dot notation (e.g. users.0.email)."
    ),
    compact: bool = typer.Option(
        False, "--compact", "-c", help="Output compact JSON without formatting."
    ),
    set_value: Optional[list[str]] = typer.Option(
        None, "--set", "-s", help="Set a value: key=value or key=@file.json."
    ),
    delete: Optional[list[str]] = typer.Option(
        None, "--del", "-d", help="Delete a key from the output."
    ),
    csv_mode: bool = typer.Option(
        False, "--csv", help="Read a CSV file and print it as a formatted table."
    ),
    delimiter: str = typer.Option(
        ",", "--delimiter", "-D", help="Column delimiter for CSV mode."
    ),
    no_header: bool = typer.Option(
        False, "--no-header", "-n", help="Treat first CSV row as data, not a header."
    ),
) -> None:
    """A CLI tool for viewing and manipulating JSON files."""
    if csv_mode:
        if not file:
            raise typer.BadParameter("A file path is required for CSV mode.")
        try:
            rows = read_csv(file, delimiter=delimiter)
        except ValueError as e:
            raise typer.BadParameter(str(e)) from e
        print_csv(rows, header=not no_header)
        return

    stdin_used = file is None
    try:
        data = read_json(file)
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e

    if set_value:
        for item in set_value:
            k, _, v = item.partition("=")
            if not k or not v:
                raise typer.BadParameter(
                    f"Invalid --set format: '{item}'. Use key=value."
                )
            if v == "@-":
                if stdin_used:
                    raise typer.BadParameter(
                        "Cannot use @- (stdin) for --set when stdin is already used as primary input."
                    )
                v = json.load(sys.stdin)
            elif v.startswith("@"):
                with open(v[1:]) as f:
                    v = json.load(f)
            else:
                try:
                    v = json.loads(v)
                except json.JSONDecodeError:
                    pass  # keep as string
            data = update_json(data, k, v)

    if delete:
        from jspprint.io import _traverse

        for k in delete:
            try:
                parent, last_key = _traverse(data, k, stop_before_last=True)
                if isinstance(parent, dict) and last_key in parent:
                    del parent[last_key]
                elif isinstance(parent, list) and last_key.isdigit():
                    del parent[int(last_key)]
                else:
                    raise KeyError(f"Key '{k}' not found in the data.")
            except KeyError as e:
                raise typer.BadParameter(str(e)) from e

    if key:
        try:
            data = filter_by_key(data, key)
        except KeyError as e:
            raise typer.BadParameter(str(e)) from e

    print_json(data, pretty=not compact)


if __name__ == "__main__":
    app()
