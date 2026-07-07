"""Introspect a live ROS2 graph into a plain dict of facts.

These facts are the *ground truth* the LLM Wiki is allowed to describe. The
generator must not add anything not present here — that's how we keep the wiki
grounded and free of hallucinated topics/nodes.
"""
from typing import Dict, List


def collect_graph(node) -> Dict:
    """Walk the ROS2 graph visible from ``node`` and return a facts dict."""
    graph: Dict = {"nodes": {}, "topics": {}, "services": {}}

    for tname, ttypes in node.get_topic_names_and_types():
        graph["topics"][tname] = list(ttypes)
    for sname, stypes in node.get_service_names_and_types():
        graph["services"][sname] = list(stypes)

    for nname, ns in node.get_node_names_and_namespaces():
        if nname == node.get_name():
            continue  # skip the introspector itself
        try:
            pubs = node.get_publisher_names_and_types_by_node(nname, ns)
            subs = node.get_subscriber_names_and_types_by_node(nname, ns)
            srvs = node.get_service_names_and_types_by_node(nname, ns)
        except Exception:  # noqa: BLE001 - node may vanish mid-scan
            pubs, subs, srvs = [], [], []
        graph["nodes"][nname] = {
            "namespace": ns,
            "publishers": _fmt(pubs),
            "subscribers": _fmt(subs),
            "services": _fmt(srvs),
        }
    return graph


def _fmt(pairs) -> List[Dict]:
    return [{"name": name, "types": list(types)} for name, types in pairs]
