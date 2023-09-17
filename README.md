# nats demo

nats demo running in a local kubernetes cluster.

## Getting started

Prerequisites:

- [k3d](https://k3d.io/) (for creating a local kubernetes cluster)
- kubectl
- helm

Create k3d cluster and deploy nats:

```
make kubes
```

## Usage

Endpoints:

- nats: tcp://localhost:4222
- nats monitor: [http://localhost:8222](http://localhost:8222)

## References

- [NATS Server Helm chart](https://artifacthub.io/packages/helm/nats/nats)
- [NATS Protocol Demo](https://docs.nats.io/reference/reference-protocols/nats-protocol-demo)
