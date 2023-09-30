# nats demo

nats demo running in a local kubernetes cluster.

## Getting started

Prerequisites:

- [k3d](https://k3d.io/) (for creating a local kubernetes cluster)
- kubectl
- helm

Install nats cli, create k3d cluster and deploy nats:

```
make install
```

## Usage

Endpoints:

- nats: tcp://localhost:4222
- nats monitor: [http://localhost:8222](http://localhost:8222)

Run

- `make ping`
- `make demo-js` python [jetstream demo](src/demo/js.py)
- `nats stream ls` list streams
- `nats server report connections` list connections
- `nats server ls --context=admin` list servers using system account (admin)
- `nats server report jetstream --context=admin` jetstream summary report
- `nats kv watch articles` tail bucket `dwatch`
- `nats stream view KV_dwatch` view messages in the `KV_dwatch` stream
- `nats stream get KV_dwatch 2` view message with sid 2 in `KV_dwatch` stream
- `nats consumer rm KV_dwatch` delete consumer. Recreating it will start from the beginning of the stream.
- `nats events -a` listen for advisories eg: delivery attempts exceeded

## Config

Stored in /etc/nats-config/nats.conf.

NB: /etc/nats/nats-server.conf is the [default example config](https://github.com/nats-io/nats-docker/blob/main/2.9.x/alpine3.18/nats-server.conf) built into the docker image.

## References

- [How NATS stores data on disk](docs/filestore.md)
- [NATS Server Helm chart](https://artifacthub.io/packages/helm/nats/nats)
- [NATS Protocol Demo](https://docs.nats.io/reference/reference-protocols/nats-protocol-demo)
- [NATS cli](https://docs.nats.io/using-nats/nats-tools/nats_cli)
- [NATS configuration](https://docs.nats.io/running-a-nats-service/configuration)

## Troubleshooting

### nats: error: server request failed, ensure the account used has system privileges and appropriate permissions

Connect using the system account.

### nats: error: nats: Authorization Violation

Use the username and password when connecting, eg:
