# ROS2 Quality of Service (QoS)

## What QoS is
ROS2 runs on DDS, which lets each publisher and subscription declare a Quality of
Service (QoS) profile describing how messages should be delivered. QoS matters
because a publisher and a subscription only exchange messages if their QoS
profiles are **compatible**. A mismatch is one of the most common reasons a
subscriber receives nothing even though the publisher is clearly running.

## Key QoS policies
- **Reliability**
  - `RELIABLE` — guarantees delivery, retransmitting if needed. Good for
    commands and services where every message must arrive.
  - `BEST_EFFORT` — sends without delivery guarantees; faster and lower
    overhead. Common for high-rate sensor data where an occasional dropped
    message is acceptable.
- **Durability**
  - `VOLATILE` — subscribers only get messages published after they connect.
  - `TRANSIENT_LOCAL` — the publisher stores the last messages so late-joining
    subscribers still receive them. Used for latched data like a map or a robot
    description that is published once.
- **History**
  - `KEEP_LAST` with a depth N — buffer the last N messages.
  - `KEEP_ALL` — buffer everything (bounded by resource limits).

## The classic mismatch pitfall
A `BEST_EFFORT` publisher and a `RELIABLE` subscription are **incompatible** — the
subscription will not receive the publisher's messages. Sensor drivers often
publish `BEST_EFFORT`; if your subscription defaults to `RELIABLE`, you silently
get nothing. The fix is to match the profiles: subscribe with a compatible QoS
(e.g. use the `SensorDataQoS` profile for sensor topics). When debugging "my
subscriber gets no messages," check QoS compatibility before anything else.
