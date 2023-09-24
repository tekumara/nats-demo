# adapted from https://github.com/nats-io/nats.py/blob/635fb2e/tests/test_js.py#L2345

import asyncio
import nats
import nats.errors
import nats.js.errors

errors = []


async def main():
    async def error_handler(e):
        print("Error:", e, type(e))
        errors.append(e)

    nc = await nats.connect(name="watcher-1", error_cb=error_handler)
    js = nc.jetstream()

    try:
        kv = await js.delete_key_value(bucket="dwatch")
    except nats.js.errors.NotFoundError:
        pass

    kv = await js.create_key_value(bucket="dwatch", replicas=3)
    status = await kv.status()
    print(status)
    print(kv._stream)

    await kv.create("new", b"hello world")
    await kv.put("t.name", b"alex")
    await kv.put("t.name", b"bob")

    await kv.put("t.age", b"20")
    await kv.put("t.age", b"21")
    await kv.put("t.a", b"a")
    await kv.delete("t.a")
    await kv.put("t.b", b"b")

    # Create pull based consumer
    psub = await js.pull_subscribe(
        subject="$KV.dwatch.>",
        durable="psub",
        stream="KV_dwatch",
        # will redeliver if not acked within 1 second
        config=nats.js.api.ConsumerConfig(ack_wait=1),
    )

    # Fetch and ack messages from consumer.
    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.subject == "$KV.dwatch.new"
    assert msg.data == b"hello world"
    await msg.ack()

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"bob"
    await msg.ack()

    # interleave
    await kv.put("t.c", b"c")
    await kv.put("t.d", b"d")

    # close and reconnect
    await nc.close()
    nc = await nats.connect(name="watcher-2", error_cb=error_handler)
    js = nc.jetstream()
    # NB: config is only used when the consumer is first created
    psub = await js.pull_subscribe(
        subject="$KV.dwatch.>", durable="psub", stream="KV_dwatch"
    )

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"21"
    await msg.ack()

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.subject == "$KV.dwatch.t.a"
    assert msg.headers and msg.headers["KV-Operation"] == "DEL"
    assert msg.data == b""
    await msg.ack()

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"b"
    # don't ack, will be redelivered after ack_wait

    # in meantime we can still get c next
    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"c"
    await msg.ack()

    await asyncio.sleep(1)

    # b is back
    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.subject == "$KV.dwatch.t.b"
    assert msg.data == b"b"
    await msg.ack()

    # fetch batch bigger than stream contents
    # will wait to get up to 100 messages or timeout and return whatever
    # it can find
    print("fetch big batch")
    msgs = await psub.fetch(100, timeout=0.5)
    print(msgs)
    assert len(msgs) == 1
    msg = msgs[0]
    assert msg.subject == "$KV.dwatch.t.d"
    assert msg.data == b"d"
    await msg.ack()

    # TODO: two subs to same consumer


    # At the end of the stream, subsequent watch attempts will be a timeout error.
    try:
        (msg,) = await psub.fetch(1, timeout=0.5)
        raise Exception("did not timeout")
    except nats.errors.TimeoutError:
        pass

    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
