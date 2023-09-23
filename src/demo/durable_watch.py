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

    nc = await nats.connect(error_cb=error_handler)
    js = nc.jetstream()

    try:
        kv = await js.delete_key_value(bucket="DWATCH")
    except nats.js.errors.NotFoundError:
        pass

    kv = await js.create_key_value(bucket="DWATCH", replicas=3)
    status = await kv.status()
    print(status)

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
        subject="$KV.DWATCH.>", durable="psub", stream="KV_DWATCH",
        config = nats.js.api.ConsumerConfig(ack_wait=1)
    )

    # Fetch and ack messages from consumer.
    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.subject == "$KV.DWATCH.new"
    assert msg.data == b"hello world"
    await msg.ack()

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"bob"
    await msg.ack()

    # interleave
    await kv.put("t.c", b"c")

    # close and reconnect
    await nc.close()
    nc = await nats.connect(error_cb=error_handler)
    js = nc.jetstream()
    psub = await js.pull_subscribe(
        subject="$KV.DWATCH.>", durable="psub", stream="KV_DWATCH"
    )

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"21"
    await msg.ack()

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.subject == "$KV.DWATCH.t.a"
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
    assert msg.subject == "$KV.DWATCH.t.b"
    assert msg.data == b"b"
    await msg.ack()

    # After getting the None marker, subsequent watch attempts will be a timeout error.
    try:
        (msg,) = await psub.fetch(1, timeout=0.5)
        raise Exception("did not timeout")
    except nats.errors.TimeoutError as e:
        pass

    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
