"""Example 16: Dependency injection via inject parameter."""

import sys
import logging
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tranq

logger = logging.getLogger("demo_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("   [%(name)s] %(message)s"))
    logger.addHandler(handler)

config = {"db_host": "localhost", "db_port": 5432}

@tranq.handle(inject={"logger": logger, "config": config})
def database_operation(logger=None, config=None):
    logger.info(f"Connecting to {config['db_host']}:{config['db_port']}")
    return "connected"

print("1) Injected logger and config:")
result = database_operation()
print(f"   Result: {result}")
print()

# Explicit kwargs override injection
print("2) Explicit argument overrides injection:")
result = database_operation(config={"db_host": "remotehost", "db_port": 3306})
print(f"   Result: {result}")
print()

# Async injection
@tranq.handle_async(inject={"service_name": "payment-gateway"})
async def async_service(service_name=None):
    return f"async connected to {service_name}"

print("3) Async injection:")
result = asyncio.run(async_service())
print(f"   Result: {result}")
