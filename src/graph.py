from langgraph.graph import END, START, StateGraph

from nodes.fly_fishing import fly_fishing
from nodes.growth import growth
from nodes.orchestrator import ALL_DOMAINS, route, route_decision, synthesize
from nodes.personal_system import personal_system_check
from nodes.physical import physical
from nodes.restoration import restoration
from state import State

_DOMAIN_NODES = {
    "fly_fishing": fly_fishing,
    "physical": physical,
    "restoration": restoration,
    "growth": growth,
}


def build_graph():
    builder = StateGraph(State)

    builder.add_node("personal_system_check", personal_system_check)
    builder.add_node("route_decision", route_decision)
    for name, fn in _DOMAIN_NODES.items():
        builder.add_node(name, fn)
    builder.add_node("synthesize", synthesize)

    builder.add_edge(START, "personal_system_check")
    builder.add_edge("personal_system_check", "route_decision")
    builder.add_conditional_edges(
        "route_decision", route, list(_DOMAIN_NODES.keys())
    )
    for name in ALL_DOMAINS:
        builder.add_edge(name, "synthesize")
    builder.add_edge("synthesize", END)

    return builder.compile()
