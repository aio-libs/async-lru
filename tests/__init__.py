import os

os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['PYTHONASYNCIODEBUG'] = '1'

import asyncio

asyncio.set_event_loop(None)
