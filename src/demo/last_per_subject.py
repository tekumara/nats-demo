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

    # keep max two versions
    kv = await js.create_key_value(bucket="dwatch", replicas=3, history=2)
    status = await kv.status()
    print(status)
    print(kv._stream)

    await kv.put("t.age", b"20")
    await kv.put("t.age", b"21")

    # with DeliverLastPerSubject we only get the latest version
    psub = await js.pull_subscribe(
        subject="$KV.dwatch.>",
        durable="psub",
        stream="KV_dwatch",
        # will redeliver if not acked within 1 second
        config=nats.js.api.ConsumerConfig(ack_wait=1,deliver_policy=nats.js.api.DeliverPolicy.LAST_PER_SUBJECT),
    )


    # We get latest when the consumer starts
    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"21", msg.data
    await msg.ack()

    # And then history from then on
    await kv.put("t.age", b"22")
    await kv.put("t.age", b"23")

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"22", msg.data
    await msg.ack()

    (msg,) = await psub.fetch(1)
    print(msg)
    assert msg.data == b"23", msg.data
    await msg.ack()

    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
