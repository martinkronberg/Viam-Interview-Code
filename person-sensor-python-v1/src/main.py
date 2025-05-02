import asyncio
from viam.module.module import Module
try:
    from models.person_sensor import PersonSensor
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.person_sensor import PersonSensor


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
