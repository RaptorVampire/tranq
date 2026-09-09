.. _changelog:

=========
Changelog
=========

See `CHANGELOG.md <https://github.com/RaptorVampire/tranq/blob/main/CHANGELOG.md>`_
for full release history.

Latest: **v1.1.0**
------------------

**Resilience Platform** release with:

* Composable retry primitives (wait/stop/retry_if)
* Cache with stampede prevention
* 5 rate limiting algorithms
* 4 bulkhead types
* Policy composition DSL
* Adaptive resilience
* Presets for HTTP/DB/Redis/Kafka/gRPC/LLM
* HTTP intelligence (Retry-After)
* OpenTelemetry native
* Unified event bus (14 event types)
* Distributed state (Redis)
* Dependency graph
* Chaos testing framework
* LLM resilience + provider failover
* Auto policy detection
* 190+ tests


v1.0.0
------

Production/Stable release with timeouts, event hooks, sliding-window CB,
rate limiter, bulkhead, retry budget, hedged requests, advanced metrics
(p50/p95/p99), statistics, reporters, async context manager, PEP 561 typing.


v0.3.0
------

Initial public release with decorators, backoff strategies, circuit breakers,
context manager, retry groups, metrics, profiling, reporters, mock errors,
dependency injection, global policy, stateful retry.
