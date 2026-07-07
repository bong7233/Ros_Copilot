# ROS2 Core Concepts

## Nodes
A node is a single process that performs computation in a ROS2 system. Nodes are
the fundamental building blocks; a robot application is typically composed of
many nodes, each responsible for one job (e.g. reading a sensor, running a
controller, planning a path). Nodes discover each other automatically over DDS.

## Topics (publish/subscribe)
Topics are named buses over which nodes exchange messages using a
publish/subscribe model. A publisher sends messages on a topic without knowing
who (if anyone) is listening; subscribers receive every message on topics they
subscribe to. Topics are best for continuous data streams such as sensor
readings (`/scan`, `/odom`) or velocity commands (`/cmd_vel`). Communication is
many-to-many and asynchronous.

## Services (request/response)
Services provide synchronous request/response calls between nodes. A client
sends a request and blocks until the server returns a response. Services suit
short, infrequent operations where you need a direct answer — for example
querying a knowledge base or asking a node to perform a quick, bounded action.
Unlike topics, a service call has exactly one response per request.

## Actions (long-running goals)
Actions are for long-running tasks that produce periodic feedback and can be
cancelled — for example "navigate to a pose" or "pick up an object". An action
has three parts: a goal (sent by the client), feedback (streamed while the task
runs), and a result (returned when it finishes). Nav2's `NavigateToPose` is an
action. Use actions when a task takes time and you want progress updates or the
ability to preempt it.

## Parameters
Parameters are named, typed configuration values attached to a node (e.g. a
speed limit, a file path, a topic name). They can be set at launch or changed at
runtime, letting you reconfigure a node without editing code.

## When to use which
- Continuous stream of data, many listeners -> **topic**
- Quick request that needs one answer -> **service**
- Long task with feedback and cancellation -> **action**
- Node configuration value -> **parameter**
