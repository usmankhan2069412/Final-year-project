from app.main import app


def test_agents_sse_stream_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/api/v1/agents/stream" in paths
    assert "/api/v1/agents/conversations/stream" in paths
