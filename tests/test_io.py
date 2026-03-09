import json

import pytest

from jsp.io import filter_by_key, print_json, update_json


class TestFilterByKey:
    def test_top_level_key(self):
        data = {"name": "test", "value": 42}
        assert filter_by_key(data, "name") == {"name": "test"}

    def test_nested_key(self):
        data = {"a": {"b": {"c": "deep"}}}
        assert filter_by_key(data, "a.b.c") == {"a.b.c": "deep"}

    def test_array_index(self):
        data = {"users": [{"name": "alice"}, {"name": "bob"}]}
        assert filter_by_key(data, "users.1.name") == {"users.1.name": "bob"}

    def test_array_index_returns_element(self):
        data = {"items": ["a", "b", "c"]}
        assert filter_by_key(data, "items.0") == {"items.0": "a"}

    def test_array_index_out_of_range(self):
        data = {"items": ["a", "b"]}
        with pytest.raises(KeyError, match="out of range"):
            filter_by_key(data, "items.5")

    def test_missing_top_level_key(self):
        data = {"name": "test"}
        with pytest.raises(KeyError, match="not found"):
            filter_by_key(data, "missing")

    def test_missing_nested_key(self):
        data = {"a": {"b": 1}}
        with pytest.raises(KeyError, match="not found"):
            filter_by_key(data, "a.c")

    def test_nested_array_of_objects(self):
        data = {"users": [{"emails": ["a@b.com", "c@d.com"]}]}
        assert filter_by_key(data, "users.0.emails.1") == {"users.0.emails.1": "c@d.com"}

    def test_returns_subtree(self):
        data = {"a": {"b": {"c": 1, "d": 2}}}
        assert filter_by_key(data, "a.b") == {"a.b": {"c": 1, "d": 2}}


class TestUpdateJson:
    def test_set_top_level_key(self):
        data = {"name": "old"}
        result = update_json(data, "name", "new")
        assert result["name"] == "new"

    def test_set_nested_key(self):
        data = {"a": {"b": {"c": 1}}}
        result = update_json(data, "a.b.c", 99)
        assert result["a"]["b"]["c"] == 99

    def test_add_new_key(self):
        data = {"a": 1}
        result = update_json(data, "b", 2)
        assert result == {"a": 1, "b": 2}

    def test_set_array_element(self):
        data = {"items": ["a", "b", "c"]}
        result = update_json(data, "items.1", "updated")
        assert result["items"] == ["a", "updated", "c"]

    def test_set_nested_in_array(self):
        data = {"users": [{"name": "alice"}, {"name": "bob"}]}
        result = update_json(data, "users.0.name", "alicia")
        assert result["users"][0]["name"] == "alicia"

    def test_set_dict_value(self):
        data = {"config": {}}
        result = update_json(data, "config", {"key": "value"})
        assert result["config"] == {"key": "value"}

    def test_array_index_out_of_range(self):
        data = {"items": ["a"]}
        with pytest.raises(KeyError, match="out of range"):
            update_json(data, "items.5", "x")

    def test_missing_intermediate_key(self):
        data = {"a": 1}
        with pytest.raises(KeyError, match="not found"):
            update_json(data, "b.c", "x")


class TestPrintJson:
    def test_pretty_output(self, capsys):
        data = {"key": "value"}
        print_json(data, pretty=False)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

    def test_compact_is_single_line(self, capsys):
        data = {"key": "value", "nested": {"a": 1}}
        print_json(data, pretty=False)
        captured = capsys.readouterr()
        assert "\n" not in captured.out.strip()
