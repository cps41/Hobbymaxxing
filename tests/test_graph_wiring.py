from hobbymaxxing.graph import build_graph


def test_graph_runs_end_to_end_with_stubs():
    graph = build_graph()
    result = graph.invoke({"run_timestamp": "2026-08-13T18:00:00", "horizon": "today"})

    assert "final_recommendation" in result
    assert result["final_recommendation"]["hobby"]


def test_router_skips_fly_fishing_when_dark():
    graph = build_graph()
    result = graph.invoke({"run_timestamp": "2026-08-13T21:00:00", "horizon": "today"})

    assert "fly_fishing" not in result["active_domains"]
    assert result.get("fly_fishing_suggestion") is None
    assert "fly_fishing" in result["skip_reasons"]
