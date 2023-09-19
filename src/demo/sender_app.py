from panini import app as panini_app

app = panini_app.App(
    service_name="sender_app",
    host="127.0.0.1",
    port=4222,
)


@app.task(interval=1)
async def request_periodically():
    message = {"data": "request1234567890"}
    response = await app.request(
        subject="some.subject.for.request",
        message=message,
    )
    print(response)


@app.task(interval=1)
async def publish_periodically():
    message = {"data": "event1234567890"}
    await app.publish(
        subject="some.subject.for.stream",
        message=message,
    )


if __name__ == "__main__":
    app.start()
