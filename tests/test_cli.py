import json
import tempfile

from typer.testing import CliRunner

from jspprint.cli import app

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


def test_invalid_json_stdin():
    result = runner.invoke(app, input="not valid json")
    assert result.exit_code != 0
    assert "Invalid JSON" in result.output


def test_set_json_object_value():
    data = {"config": {}}
    result = runner.invoke(
        app, ["--compact", "--set", 'config={"one": "value", "two": 2}'],
        input=json.dumps(data),
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["config"] == {"one": "value", "two": 2}


def test_set_json_array_value():
    data = {"items": []}
    result = runner.invoke(
        app, ["--compact", "--set", "items=[1, 2, 3]"], input=json.dumps(data)
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["items"] == [1, 2, 3]


def test_set_json_number_value():
    data = {"count": 0}
    result = runner.invoke(
        app, ["--compact", "--set", "count=42"], input=json.dumps(data)
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["count"] == 42


def test_set_json_boolean_value():
    data = {"enabled": True}
    result = runner.invoke(
        app, ["--compact", "--set", "enabled=false"], input=json.dumps(data)
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["enabled"] is False


# CSV tests


def test_csv_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        f.flush()
        result = runner.invoke(app, ["--csv", f.name])
    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "Bob" in result.output


def test_csv_custom_delimiter():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("a;b;c\n1;2;3\n")
        f.flush()
        result = runner.invoke(app, ["--csv", "-D", ";", f.name])
    assert result.exit_code == 0
    assert "1" in result.output


def test_csv_no_header():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("1,2,3\n4,5,6\n")
        f.flush()
        result = runner.invoke(app, ["--csv", "--no-header", f.name])
    assert result.exit_code == 0
    assert "1" in result.output
    assert "4" in result.output


def test_csv_requires_file():
    result = runner.invoke(app, ["--csv"])
    assert result.exit_code != 0
