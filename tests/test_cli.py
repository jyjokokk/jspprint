import json
import tempfile

from typer.testing import CliRunner

from jsp.cli import app

runner = CliRunner()


def test_read_from_file():
    data = {"name": "test", "value": 42}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = runner.invoke(app, [f.name])

    assert result.exit_code == 0
    assert '"name"' in result.output
    assert '"test"' in result.output


def test_read_from_stdin():
    data = {"hello": "world"}
    result = runner.invoke(app, input=json.dumps(data))
    assert result.exit_code == 0
    assert '"hello"' in result.output
    assert '"world"' in result.output


def test_no_input_shows_error():
    result = runner.invoke(app)
    assert result.exit_code != 0


def test_invalid_json_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json")
        f.flush()
        result = runner.invoke(app, [f.name])

    assert result.exit_code != 0


def test_nonexistent_file():
    result = runner.invoke(app, ["/tmp/does_not_exist_jsp_test.json"])
    assert result.exit_code != 0


def test_nested_json():
    data = {"a": {"b": {"c": "deep"}}}
    result = runner.invoke(app, input=json.dumps(data))
    assert result.exit_code == 0
    assert '"deep"' in result.output


def test_compact_output():
    data = {"name": "test", "value": 42}
    result = runner.invoke(app, ["--compact"], input=json.dumps(data))
    assert result.exit_code == 0
    assert "\n" not in result.output.strip()


def test_filter_by_key():
    data = {"name": "test", "value": 42}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = runner.invoke(app, [f.name, "name", "--compact"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"name": "test"}


def test_filter_by_nested_key():
    data = {"a": {"b": {"c": "deep"}}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = runner.invoke(app, [f.name, "a.b.c", "--compact"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"a.b.c": "deep"}


def test_filter_missing_key():
    data = {"name": "test"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = runner.invoke(app, [f.name, "missing"])
    assert result.exit_code != 0


def test_set_value():
    data = {"name": "old", "value": 1}
    result = runner.invoke(app, ["--compact", "--set", "name=new"], input=json.dumps(data))
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["name"] == "new"


def test_set_json_value():
    data = {"config": {}}
    result = runner.invoke(
        app, ["--compact", "--set", 'config={"a":1}'], input=json.dumps(data)
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["config"] == {"a": 1}


def test_set_from_file():
    data = {"config": {}}
    override = {"key": "from_file"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(override, f)
        f.flush()
        result = runner.invoke(
            app, ["--compact", "--set", f"config=@{f.name}"], input=json.dumps(data)
        )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["config"] == {"key": "from_file"}


def test_delete_key():
    data = {"name": "test", "value": 42}
    result = runner.invoke(app, ["--compact", "--del", "value"], input=json.dumps(data))
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert "value" not in parsed
    assert parsed["name"] == "test"


def test_delete_missing_key():
    data = {"name": "test"}
    result = runner.invoke(app, ["--del", "missing"], input=json.dumps(data))
    assert result.exit_code != 0


def test_set_from_stdin_with_file_input():
    """When primary input is a file, @- should read from stdin."""
    data = {"config": {}}
    override = {"from": "stdin"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = runner.invoke(
            app, [f.name, "--compact", "--set", "config=@-"], input=json.dumps(override)
        )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["config"] == {"from": "stdin"}


def test_set_from_stdin_when_stdin_is_primary_input():
    """When stdin is primary input, @- should error."""
    data = {"config": {}}
    result = runner.invoke(app, ["--set", "config=@-"], input=json.dumps(data))
    assert result.exit_code != 0
    assert "stdin" in result.output.lower()


def test_set_from_file_when_stdin_is_primary_input():
    """When stdin is primary input, @file.json should still work."""
    data = {"config": {}}
    override = {"key": "from_file"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(override, f)
        f.flush()
        result = runner.invoke(
            app, ["--compact", "--set", f"config=@{f.name}"], input=json.dumps(data)
        )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["config"] == {"key": "from_file"}
