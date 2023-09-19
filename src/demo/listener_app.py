from panini import app as panini_app

app = panini_app.App(
    service_name="listener_app",
    host="127.0.0.1",
    port=4222,
)


@app.listen("some.subject.for.request")
async def request_listener(msg):
    """request endpoint"""
    print(f"request {msg.data} from {msg.subject} has been processed")
    return {"success": True, "message": "request has been processed"}


@app.listen("some.subject.for.stream")
async def stream_listener(msg):
    """stream endpoint"""
    print(f"event {msg.data} from {msg.subject} has been processed")


if __name__ == "__main__":
    app.start()
