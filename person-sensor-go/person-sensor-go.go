package personsensorgo

import (
	"context"
	"errors"

	"go.viam.com/rdk/components/camera"
	"go.viam.com/rdk/components/sensor"
	"go.viam.com/rdk/logging"
	"go.viam.com/rdk/resource"
	"go.viam.com/rdk/services/vision"
	"go.viam.com/utils/rpc"
)

var (
	PersonSensorGo   = resource.NewModel("martin-namespace", "person-sensor-go", "person-sensor-go")
	errUnimplemented = errors.New("unimplemented")
)

func init() {
	resource.RegisterComponent(sensor.API, PersonSensorGo,
		resource.Registration[sensor.Sensor, *Config]{
			Constructor: newPersonSensorGo,
		},
	)
}

// -----------------------------------------------------------------------------
// Config
// -----------------------------------------------------------------------------

type Config struct {
	CameraName    string `json:"camera_name"`
	VisionService string `json:"vision_service"`
}

func (c *Config) Validate(path string) ([]string, error) {
	if c.CameraName == "" {
		return nil, resource.NewConfigValidationFieldRequiredError(path, "camera_name")
	}
	if c.VisionService == "" {
		return nil, resource.NewConfigValidationFieldRequiredError(path, "vision_service")
	}
	return []string{c.CameraName, c.VisionService}, nil
}

// -----------------------------------------------------------------------------
// Sensor implementation
// -----------------------------------------------------------------------------

type personSensor struct {
	resource.AlwaysRebuild
	name   resource.Name
	logger logging.Logger
	cfg    *Config

	cam    camera.Camera
	vision vision.Service
	cancel context.CancelFunc
}

func newPersonSensorGo(
	ctx context.Context,
	deps resource.Dependencies,
	raw resource.Config,
	logger logging.Logger,
) (sensor.Sensor, error) {

	cfg, err := resource.NativeConfig[*Config](raw)
	if err != nil {
		return nil, err
	}
	cam, err := camera.FromDependencies(deps, cfg.CameraName)
	if err != nil {
		return nil, err
	}
	vis, err := vision.FromDependencies(deps, cfg.VisionService)
	if err != nil {
		return nil, err
	}

	ctx, cancel := context.WithCancel(ctx)
	return &personSensor{
		name:   raw.ResourceName(),
		logger: logger,
		cfg:    cfg,
		cam:    cam,
		vision: vis,
		cancel: cancel,
	}, nil
}

func (s *personSensor) Name() resource.Name { return s.name }

// remote-client constructor
func (s *personSensor) NewClientFromConn(
	ctx context.Context,
	conn rpc.ClientConn,
	remoteName string,
	name resource.Name,
	logger logging.Logger,
) (sensor.Sensor, error) {
	return sensor.NewClientFromConn(ctx, conn, remoteName, name, logger)
}

func (s *personSensor) Readings(
	ctx context.Context,
	extra map[string]interface{},
) (map[string]interface{}, error) {

	dets, err := s.vision.DetectionsFromCamera(ctx, s.cfg.CameraName, extra)
	if err != nil {
		s.logger.Warnw("vision error", "err", err)
			// treat errors as “no person”
		return map[string]interface{}{"person_detected": 0}, nil
	}
	detected := 0          // default: nobody found
	if len(dets) > 0 {     // any detections?
    detected = 1
	}

	return map[string]interface{}{
    "person_detected": detected,
		}, nil
	}

func (s *personSensor) DoCommand(ctx context.Context, cmd map[string]interface{}) (map[string]interface{}, error) {
	return nil, errUnimplemented
}

func (s *personSensor) Close(ctx context.Context) error {
	s.cancel()
	return nil
}

