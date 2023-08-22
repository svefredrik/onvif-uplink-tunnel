# ONVIF Uplink PoC

This this a proof-of-concept implementation of the device-side of the [ONVIF Uplink Spec](https://www.onvif.org/specs/srv/uplink/ONVIF-Uplink-Spec.pdf).

## Requirements

* Axis device
  * Chip: ARTPEC-{7-8} DLPU devices (e.g., Q1615 MkIII)
  * Firmware: 10.9 or higher
  * [Docker ACAP](https://github.com/AxisCommunications/docker-acap) installed and started, using TLS and SD card as storage
* Computer
  * Either [Docker Desktop](https://docs.docker.com/desktop/) version 4.11.1 or higher,
  * or [Docker Engine](https://docs.docker.com/engine/) version 20.10.17 or higher with BuildKit enabled using Docker Compose version 1.29.2 or higher

### Include the Apache config

Copy the Apache config fragment to the target. This will enable h2 and h2c on 127.0.0.6 and set a 600 keep alive timeout on that address. This is to avoid having to reconnect constantly.

```sh
export DEVICE_IP=<actual camera IP address>
scp localhost-h2c.conf root@$DEVICE_IP:/etc/apache2/conf.d
```

Restart Apache:

```sh
ssh root@$DEVICE_IP "systemctl restart httpd"
```

## Building and running the image

### Export the environment variable for the architecture

Export the `ARCH` variable depending on the architecture of your camera:

```sh
# For arm32
export ARCH=armv7hf

# For arm64
export ARCH=aarch64
```

### Build the Docker image

```sh
# Define app name
export APP_NAME=onvif-uplink-tunnel

docker build --tag $APP_NAME --build-arg ARCH .
```

### Set your device IP address and clear Docker memory

```sh
export DOCKER_PORT=2376

docker --tlsverify --host tcp://$DEVICE_IP:$DOCKER_PORT system prune --all --force
```

If you encounter any TLS related issues, please see the TLS setup chapter regarding the `DOCKER_CERT_PATH` environment variable in the [Docker ACAP repository](https://github.com/AxisCommunications/docker-acap).

### Install the image

Next, the built image needs to be uploaded to the device. This can be done through a registry or directly. In this case, the direct transfer is used by piping the compressed application directly to the device's docker client:

```sh
docker save $APP_NAME | docker --tlsverify --host tcp://$DEVICE_IP:$DOCKER_PORT load
```

### Run the container

With the application image on the device, it can be started using `docker-compose.yml`:

```sh
docker --tlsverify --host tcp://$DEVICE_IP:$DOCKER_PORT compose up

# Cleanup
docker --tlsverify --host tcp://$DEVICE_IP:$DOCKER_PORT compose down
```

## License

**[Apache License 2.0](../LICENSE)**
