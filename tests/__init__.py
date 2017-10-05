import os  # noqa # isort:skip
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['PYTHONASYNCIODEBUG'] = '1'
# =======================================
import logging  # noqa # isort:skip
logging.basicConfig(level=logging.DEBUG)
# =======================================
import asyncio  # noqa # isort:skip
asyncio.set_event_loop(None)
