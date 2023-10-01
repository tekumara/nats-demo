# How NATS stores data on disk

Jetstream is stored as an append only log of blocks containing messages, with stats/index.

```
/ # tree /data/jetstream/\$G/streams/KV_DWATCH/
/data/jetstream/$G/streams/KV_DWATCH/
├── meta.inf
├── meta.sum
├── msgs
│   ├── 1.blk
│   ├── 1.fss
│   └── 1.idx
└── obs
    └── psub
        ├── meta.inf
        ├── meta.sum
        └── o.dat
```

`msgs` contains

- .blk - [load](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L1214), [append](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L2798), [compat](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L3580), [find message](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L2115)
- .idx - [index](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L5794C21-L5794C34) - contains stats like number of msgs, first and last sequence.
- .fss - SimpleState is [per subject state](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L2419C4-L2419C4), holds [number of messages and first and last seq](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/store.go#L159).

`obs` are the consumers:

- meta.inf - [metadata](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L7535C42-L7535C42)
- meta.inf - checksum

[StreamStore](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/store.go#L84) is an interface to the filestore and memstore. Methods for filestore:

- [LoadMsg](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L5559C1-L5559C1) - load message by sequence. [Binary search through blocks](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L4780), then load the message via the [write-through cache](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L238).
- [LoadNextMsg](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L5650) - load message by filter, binary search to find block with start seq, then linear scan through blocks from there.

On the consumer side, [consumer.getNextMsg](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/consumer.go#L3343) calls LoadNextMsg. The consumer will starting read from its [last seq for this subject](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/consumer.go#L306).

The above corroborates with [this comment](https://github.com/nats-io/nats-server/discussions/3772#discussioncomment-4627251):

> Subjects are indexed within a stream, so the OCC check does not add overhead, and a stream in general can grow as large as you have resources to support it. On replay to build the state of the aggregate to accept a new event, if a consumer is filtered to a specific subject, since the index is present, it only performs a linear scan over the blocks between the earliest and latest events for that subject.

And [here](https://github.com/nats-io/nats-server/discussions/3772#discussioncomment-4635952):

> As noted above, indexing is maintained to support subject-based server-side filtering for consumers.

I think the index is SimpleState being [used in firstMatching](https://github.com/nats-io/nats-server/blob/6eee1f736bb3e96d9503899c5d2b3c61e260c644/server/filestore.go#L2151).
