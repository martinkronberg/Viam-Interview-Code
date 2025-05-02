import asyncio
from typing import Any, ClassVar, Dict, Mapping, Optional

from viam.components.sensor import Sensor
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily
from viam.services.vision import VisionClient


class PersonSensor(Sensor):
    """
    Read the highest-confidence detections from a Vision service and expose a
    boolean (0/1) indicating whether a “person” was seen.
    """

    MODEL: ClassVar[Model] = Model(ModelFamily("martin-namespace", "person-sensor"), "linux")

    # --------------------------------------------------------------------- #
    # Factory

    @classmethod
    def new(
        cls,
        config: ComponentConfig,
        dependencies: Mapping[ResourceName, ResourceBase],
    ) -> "PersonSensor":
        attrs = config.attributes.fields
        vision_service_name = attrs["vision_service"].string_value
        camera_name = attrs["camera_name"].string_value

        # Look up the Vision service dependency we declared in the robot config
        vision_rn = ResourceName(namespace="rdk", type="service", subtype="vision", name=vision_service_name)
        vision = dependencies[vision_rn]  # already a VisionClient

        return cls(config.name, vision, camera_name)

    # --------------------------------------------------------------------- #
    # Instance

    def __init__(self, name: str, vision: VisionClient, camera_name: str, target_label: str = "person"):
        super().__init__(name)
        self._vision = vision
        self._camera = camera_name
        self._target = target_label.lower()

    # --------------------------------------------------------------------- #
    # Required API surface

    async def get_readings(self, extra: Optional[Dict[str, Any]] = None, **kwargs) -> Mapping[str, Any]:
        """Return {"person_detected": 1|0}."""
        detections = await self._vision.get_detections(self._camera, extra=extra)

        found = any(det.label.lower() == self._target for det in detections)
        return {"person_detected": 1 if found else 0}



if __name__ == "__main__":
    asyncio.run(_demo())
