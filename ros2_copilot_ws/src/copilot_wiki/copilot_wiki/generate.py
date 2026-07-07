"""CLI: introspect the running ROS2 graph and generate a Markdown wiki.

Run the system first (e.g. the Phase 0/2 nodes), then:
    ros2 run copilot_wiki generate --out docs/generated
    # or inspect the raw facts without calling the LLM:
    ros2 run copilot_wiki generate --dry-run
"""
import argparse
import json
import os
import time

import rclpy

from . import config
from .introspect import collect_graph
from .wiki_gen import generate_pages


def main(args=None) -> None:
    ap = argparse.ArgumentParser(
        description="Generate a grounded Markdown wiki from the live ROS2 graph.")
    ap.add_argument("--out", default=config.OUT_DIR,
                    help="output directory for the wiki")
    ap.add_argument("--model", default=config.MODEL)
    ap.add_argument("--discovery-sec", type=float, default=2.0,
                    help="how long to let graph discovery settle")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the introspected facts as JSON and exit")
    parsed = ap.parse_args(args)

    rclpy.init()
    node = rclpy.create_node("copilot_wiki")
    try:
        deadline = time.time() + parsed.discovery_sec
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        graph = collect_graph(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

    if parsed.dry_run:
        print(json.dumps(graph, indent=2))
        return

    if not graph["nodes"]:
        print("No other nodes found on the graph. Start some nodes first.")
        return

    pages = generate_pages(graph, model=parsed.model)
    os.makedirs(parsed.out, exist_ok=True)
    for rel, content in pages.items():
        path = os.path.join(parsed.out, rel)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  wrote {path}")
    print(f"\nGenerated {len(pages)} pages for {len(graph['nodes'])} nodes "
          f"in {parsed.out}")


if __name__ == "__main__":
    main()
