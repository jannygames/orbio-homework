import json

from tests.conftest import FakeGeminiClient, set_llm_client

from app.services.llm_service import StreamChunk, ToolCall


def _parse_sse(body: str) -> list[dict]:
    events = []
    for raw_event in body.strip().split("\n\n"):
        if not raw_event.strip():
            continue
        event_name = "message"
        data = None
        for line in raw_event.split("\n"):
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = json.loads(line.removeprefix("data:").strip())
        events.append({"event": event_name, "data": data})
    return events


async def test_history_is_empty_initially(client):
    response = await client.get("/api/chat/history")

    assert response.status_code == 200
    body = response.json()
    assert body["messages"] == []


async def test_chat_without_tool_call_persists_user_and_assistant_messages(app, client):
    fake_llm = FakeGeminiClient(
        turns=[
            [StreamChunk(text="Hello "), StreamChunk(text="there!")],
        ]
    )
    set_llm_client(app, fake_llm)

    response = await client.post("/api/chat", json={"message": "Hi"})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert [e["event"] for e in events] == ["token", "token", "done"]
    assert events[-1]["data"]["text"] == "Hello there!"

    history = await client.get("/api/chat/history")
    roles = [m["role"] for m in history.json()["messages"]]
    assert roles == ["user", "assistant"]


async def test_chat_with_tool_call_persists_full_history(app, client):
    fake_llm = FakeGeminiClient(
        turns=[
            [StreamChunk(tool_calls=[ToolCall(name="get_products", args={"max_price": 50})])],
            [StreamChunk(text="Here are a few options under 50 EUR.")],
        ]
    )
    set_llm_client(app, fake_llm)

    response = await client.post("/api/chat", json={"message": "What do you have under 50 EUR?"})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    event_names = [e["event"] for e in events]
    assert event_names == ["tool_call", "tool_result", "token", "done"]

    tool_call_event = events[0]
    assert tool_call_event["data"]["tool"] == "get_products"
    assert tool_call_event["data"]["args"] == {"max_price": 50}

    tool_result_event = events[1]
    assert "products" in tool_result_event["data"]["result"]

    history = await client.get("/api/chat/history")
    messages = history.json()["messages"]
    roles = [m["role"] for m in messages]
    assert roles == ["user", "tool_call", "tool_result", "assistant"]

    tool_call_msg = messages[1]
    assert tool_call_msg["tool_name"] == "get_products"
    assert json.loads(tool_call_msg["content"]) == {"max_price": 50}

    tool_result_msg = messages[2]
    assert tool_result_msg["tool_name"] == "get_products"
    assert "products" in json.loads(tool_result_msg["content"])

    assert messages[-1]["content"] == "Here are a few options under 50 EUR."


async def test_parallel_tool_calls_are_grouped_calls_then_results(app, client):
    fake_llm = FakeGeminiClient(
        turns=[
            [
                StreamChunk(
                    tool_calls=[
                        ToolCall(name="get_products", args={"category": "electronics"}),
                        ToolCall(name="list_categories", args={}),
                    ]
                )
            ],
            [StreamChunk(text="Here is what I found.")],
        ]
    )
    set_llm_client(app, fake_llm)

    response = await client.post("/api/chat", json={"message": "Show electronics and your categories"})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert [e["event"] for e in events] == [
        "tool_call",
        "tool_call",
        "tool_result",
        "tool_result",
        "token",
        "done",
    ]

    history = await client.get("/api/chat/history")
    roles = [m["role"] for m in history.json()["messages"]]
    assert roles == ["user", "tool_call", "tool_call", "tool_result", "tool_result", "assistant"]


async def test_reset_starts_a_new_conversation(app, client):
    fake_llm = FakeGeminiClient(turns=[[StreamChunk(text="Hi there!")]])
    set_llm_client(app, fake_llm)

    await client.post("/api/chat", json={"message": "Hello"})
    history_before = await client.get("/api/chat/history")
    assert len(history_before.json()["messages"]) == 2

    reset_response = await client.post("/api/chat/reset")
    assert reset_response.status_code == 200
    new_conversation_id = reset_response.json()["conversation_id"]
    assert new_conversation_id != history_before.json()["conversation_id"]

    history_after = await client.get("/api/chat/history")
    assert history_after.json()["messages"] == []
    assert history_after.json()["conversation_id"] == new_conversation_id


async def test_llm_failure_yields_error_event_not_500(app, client):
    class ExplodingLLMClient:
        async def stream_turn(self, contents, system_instruction):
            raise RuntimeError("boom")
            yield

    set_llm_client(app, ExplodingLLMClient())

    response = await client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert events[-1]["event"] == "error"
