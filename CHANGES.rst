=======
CHANGES
=======

.. towncrier release notes start


2.1.0 (2026-01-17)
==================

- Fixed cancelling of task when all tasks waiting on it have been cancelled.
- Fixed DeprecationWarning from asyncio.iscoroutinefunction.

2.0.5 (2025-03-16)
==================

- Fixed a memory leak on exceptions and minor performance improvement.

2.0.4 (2023-07-27)
==================

- Fixed an error when there are pending tasks while calling ``.cache_clear()``.

2.0.3 (2023-07-07)
==================

- Fixed a ``KeyError`` that could occur when using ``ttl`` with ``maxsize``.
- Dropped ``typing-extensions`` dependency in Python 3.11+.
