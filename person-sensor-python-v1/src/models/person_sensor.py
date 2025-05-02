
from typing import Any, ClassVar, Dict, Mapping, Optional, Sequence

from typing_extensions import Self
from viam.components.sensor import Sensor
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict, ValueTypes
from viam.services.vision import VisionClient


class PersonSensor(Sensor, EasyResource):

    MODEL: ClassVar[Model] = Model(
        ModelFamily("martin-namespace", "person-sensor"), "person-sensor"
    )

    # ------------------------------------------------------------------ #
    # Validate config and declare the implicit Vision-service dep        #
    # ------------------------------------------------------------------ #
    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        attrs = struct_to_dict(config.attributes)
        for key in ("vision_service", "camera_name"):
            if key not in attrs:
                raise ValueError(f'missing required attribute "{key}"')

        # Return the Vision service name so Viam starts it before us
        return [attrs["vision_service"]]

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        return super().new(config, dependencies)

    # ------------------------------------------------------------------ #
    # Reconfigure – capture VisionClient handle & camera name            #
    # ------------------------------------------------------------------ #
    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        attrs = struct_to_dict(config.attributes)
        self._camera: str = attrs["camera_name"]
        vs_name = attrs["vision_service"]

        # Find the Vision service we declared as a dependency
        for rname, res in dependencies.items():
            if rname.subtype == "vision" and rname.name == vs_name:
                self._vision: VisionClient = res
                break
        else:
            raise RuntimeError(f"Vision service '{vs_name}' not found among dependencies")

        return super().reconfigure(config, dependencies)

    # ------------------------------------------------------------------ #
    # Main API – return label + confidence from get_detections           #
    # ------------------------------------------------------------------ #
    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, Any]:
        detections = await self._vision.get_detections_from_camera(
            self._camera,
            timeout=timeout,
        )

        if not detections:
            return {"person_detected":0}

        top = detections[0]  # highest-confidence detection
        return {
            "person_detected":1,
            #"label": top.class_name,
            #"confidence": top.confidence,
        }

    # ------------------------------------------------------------------ #
    # Unimplemented optional APIs                                        #
    # ------------------------------------------------------------------ #
    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        self.logger.error("`do_command` is not implemented")
        raise NotImplementedError()

    async def get_geometries(
        self,
        *,
        extra: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> list[Geometry]:
        self.logger.error("`get_geometries` is not implemented")
        raise NotImplementedError()

