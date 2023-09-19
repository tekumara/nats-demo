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
        kv = await js.delete_key_value(bucket="WATCH")
    except nats.js.errors.NotFoundError:
        pass

    kv = await js.create_key_value(bucket="WATCH")
    status = await kv.status()
    print(status)

    # Same as watch all the updates.
    w = await kv.watchall()

    # First update when there are no pending entries will be None
    # to mark that there are no more pending updates.
    e = await w.updates(timeout=1)
    assert e is None, e

    await kv.create("name", b"alice:1")
    e = await w.updates()
    assert e.delta == 0
    assert e.key == "name"
    assert e.value == b"alice:1"
    assert e.revision == 1

    await kv.put("name", b"alice:2")
    e = await w.updates()
    assert e.key == "name"
    assert e.value == b"alice:2"
    assert e.revision == 2

    await kv.put("name", b"alice:3")
    e = await w.updates()
    assert e.key == "name"
    assert e.value == b"alice:3"
    assert e.revision == 3

    await kv.put("age", b"22")
    e = await w.updates()
    assert e.key == "age"
    assert e.value == b"22"
    assert e.revision == 4

    await kv.put("age", b"33")
    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.key == "age"
    assert e.value == b"33"
    assert e.revision == 5

    await kv.delete("age")
    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.key == "age"
    assert e.value == b""
    assert e.revision == 6
    assert e.operation == "DEL"

    await kv.purge("name")
    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.key == "name"
    assert e.value == b""
    assert e.revision == 7
    assert e.operation == "PURGE"

    # No new updates at this point...
    try:
        await w.updates(timeout=0.5)
        raise Exception("did not timeout")
    except nats.errors.TimeoutError as e:
        pass

    # Stop the watcher.
    await w.stop()

    # Now try wildcard matching and make sure we only get last value when starting.
    await kv.create("new", b"hello world")
    await kv.put("t.name", b"a")
    await kv.put("t.name", b"b")
    await kv.put("t.age", b"c")
    await kv.put("t.age", b"d")
    await kv.put("t.a", b"a")
    await kv.put("t.b", b"b")

    # Will only get last values of the matching keys.
    w = await kv.watch("t.*")

    # There are values present so None is _not_ sent to as an update.
    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.delta == 3
    assert e.key == "t.name"
    assert e.value == b"b"
    assert e.revision == 10
    assert e.operation == None

    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.delta == 2
    assert e.key == "t.age"
    assert e.value == b"d"
    assert e.revision == 12
    assert e.operation == None

    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.delta == 1
    assert e.key == "t.a"
    assert e.value == b"a"
    assert e.revision == 13
    assert e.operation == None

    # Consume next pending update.
    e = await w.updates()
    assert e.bucket == "WATCH"
    assert e.delta == 0
    assert e.key == "t.b"
    assert e.value == b"b"
    assert e.revision == 14
    assert e.operation == None

    # There are no more updates so client will be sent a marker to signal
    # that there are no more updates.
    e = await w.updates()
    assert e is None

    # After getting the None marker, subsequent watch attempts will be a timeout error.
    try:
        await w.updates(timeout=1)
        raise Exception("did not timeout")
    except nats.errors.TimeoutError as e:
        pass

    await kv.put("t.hello", b"hello world")
    e = await w.updates()
    assert e.delta == 0
    assert e.key == "t.hello"
    assert e.revision == 15

    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
