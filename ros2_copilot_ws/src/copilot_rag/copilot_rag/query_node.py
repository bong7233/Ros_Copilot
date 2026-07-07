"""ROS2 service node wrapping the RAG engine as copilot_msgs/srv/Query.

This is Layer 1 of the architecture: other nodes (and later the agent) call
`/copilot_rag/query` to get grounded answers.

Run (after `colcon build` + sourcing, and ingesting docs first):
    ros2 run copilot_rag query_server
    ros2 service call /copilot_rag/query copilot_msgs/srv/Query "{question: 'What is a ROS2 action?'}"

Note: the LLM call inside the callback blocks the executor for a few seconds.
That's fine for an MVP; switching to an async / multi-threaded executor is a
natural improvement later.
"""
import rclpy
from rclpy.node import Node

from copilot_msgs.srv import Query

from . import config
from .rag_engine import RagEngine
from .store import VectorStore


class QueryServer(Node):
    def __init__(self) -> None:
        super().__init__('copilot_rag')

        self.declare_parameter('db_path', config.DEFAULT_DB_PATH)
        self.declare_parameter('collection', config.DEFAULT_COLLECTION)
        self.declare_parameter('model', config.DEFAULT_MODEL)
        self.declare_parameter('top_k', config.DEFAULT_TOP_K)

        db = self.get_parameter('db_path').value
        coll = self.get_parameter('collection').value
        model = self.get_parameter('model').value
        top_k = int(self.get_parameter('top_k').value)

        self.get_logger().info(
            f"loading vector store at {db} (collection '{coll}')")
        store = VectorStore(db, coll)
        self.get_logger().info(f"collection holds {store.count()} chunks")

        self.engine = RagEngine(store, model=model, top_k=top_k)
        self.srv = self.create_service(Query, '~/query', self.on_query)
        self.get_logger().info("RAG query service ready at ~/query")

    def on_query(self, request, response):
        self.get_logger().info(f"query: {request.question}")
        try:
            answer, sources = self.engine.answer(request.question)
        except Exception as exc:  # noqa: BLE001 - surface any failure to caller
            self.get_logger().error(f"query failed: {exc}")
            response.answer = f"error: {exc}"
            response.sources = []
            return response
        response.answer = answer
        response.sources = sources
        return response


def main(args=None) -> None:
    rclpy.init(args=args)
    node = QueryServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
