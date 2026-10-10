import pytest

from sysdesignhelper.checks import RuleError, evaluate
from sysdesignhelper.design import Design


@pytest.fixture
def design():
    d = Design()
    client = d.add_block("client")
    service = d.add_block("service")
    cache = d.add_block("cache")
    database = d.add_block("database")
    d.connect(client.id, service.id)
    d.connect(service.id, cache.id).path = "read"
    d.connect(service.id, database.id)
    database.replication_factor = 3
    cache.extras["eviction_policy"] = "allkeys-lru"
    return d


def test_has_block(design):
    assert evaluate({"has_block": {"component": "cache"}}, design)
    assert not evaluate({"has_block": {"component": "message-queue"}}, design)
    assert evaluate({"has_block": {"component": ["message-queue", "cache"]}}, design)


def test_each_block_requires_at_least_one_match(design):
    rule = {"each_block": {"where": {"component": "database"}, "require": {"replication_factor": {"gte": 2}}}}
    assert evaluate(rule, design)
    assert not evaluate(rule, Design())
    design.add_block("database")
    assert not evaluate(rule, design)


def test_extras_and_matchers(design):
    present = {"each_block": {"where": {"component": "cache"},
                              "require": {"extras.eviction_policy": {"present": True, "ne": "noeviction"}}}}
    assert evaluate(present, design)
    design.blocks[2].extras["eviction_policy"] = "NoEviction"
    assert not evaluate(present, design)
    design.blocks[2].extras.clear()
    assert not evaluate(present, design)


def test_connections(design):
    read = {"has_connection": {"from": {"component": "service"}, "to": {"component": "cache"},
                               "where": {"path": ["read", "both"]}}}
    assert evaluate(read, design)
    design.connections[1].path = "write"
    assert not evaluate(read, design)
    assert evaluate({"no_connection": {"from": {"component": "client"}, "to": {"component": "database"}}}, design)
    design.connect("b1", "b4")
    assert not evaluate({"no_connection": {"from": {"component": "client"}, "to": {"component": "database"}}}, design)


def test_has_path_follows_direction(design):
    forward = {"has_path": {"from": {"component": "client"}, "to": {"component": "database"}}}
    backward = {"has_path": {"from": {"component": "database"}, "to": {"component": "client"}}}
    via_cache = {"has_path": {"from": {"component": "client"}, "via": {"component": "cache"},
                              "to": {"component": "database"}}}
    assert evaluate(forward, design)
    assert not evaluate(backward, design)
    assert not evaluate(via_cache, design)
    design.connect("b3", "b4")
    assert evaluate(via_cache, design)


def test_combinators(design):
    yes = {"has_block": {"component": "cache"}}
    no = {"has_block": {"component": "event-log"}}
    assert evaluate({"any_of": [no, yes]}, design)
    assert not evaluate({"all_of": [no, yes]}, design)


def test_bad_rules_are_reported(design):
    with pytest.raises(RuleError):
        evaluate({"nonsense": {}}, design)
    with pytest.raises(RuleError):
        evaluate({"has_block": {"colour": "red"}}, design)


def test_removing_a_block_removes_its_connections(design):
    design.remove_block("b2")
    assert design.connections == []


def test_design_round_trips_through_dict(design):
    assert Design.from_dict(design.to_dict()) == design
