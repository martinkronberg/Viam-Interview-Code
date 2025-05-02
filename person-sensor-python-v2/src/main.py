import asyncio
from viam.module.module import Module
from viam.components.sensor import Sensor

from .person_sensor import PersonSensor


async def main():
    # Create the module process and register our sensor model
    module = Module.from_args()
    module.add_model_from_registry(Sensor.SUBTYPE, PersonSensor.MODEL)

    # Block here until the host tells us to exit
    await module.start()


if __name__ == "__main__":
    asyncio.run(main())

