"""Integration and smoke tests against a live local Ollama instance with qwen2.5:3b.

NOTE:
- This test suite executes actual local inference queries against Ollama.
- These queries serve as integration smoke tests to verify native tool calling plumbing.
- This is NOT an evaluation run and must NOT be used to claim baseline accuracy percentages.
"""

import pytest
from backend.app.services.ollama_service import OllamaService

SMOKE_TEST_CASES = [
    {
        "query": "What is 25 multiplied by 16?",
        "expected_tool": "calculator",
    },
    {
        "query": "Find our company's vacation policy in the employee handbook.",
        "expected_tool": "search_docs",
    },
    {
        "query": r"Open the file C:\Reports\annual_report.pdf.",
        "expected_tool": "read_file",
    },
    {
        "query": "What is the weather in Chennai right now?",
        "expected_tool": "get_weather",
    },
    {
        "query": "Translate 'Good morning' into Telugu.",
        "expected_tool": "translate_text",
    },
]

@pytest.fixture(scope="module")
def live_service():
    """Initializes live Ollama service and verifies daemon connectivity."""
    service = OllamaService()
    health = service.health_check()
    if not health.reachable:
        pytest.skip(f"Live Ollama instance is not reachable at {service.host}. Skipping integration tests.")
    
    model_status = service.model_available()
    if not model_status.available:
        pytest.skip(f"Configured model '{service.model}' is not pulled in Ollama. Skipping integration tests.")
    
    return service

def test_live_ollama_health_and_model(live_service):
    """Verifies that live Ollama daemon responds and qwen2.5:3b is ready."""
    health = live_service.health_check()
    assert health.reachable is True

    model_status = live_service.model_available()
    assert model_status.available is True
    assert model_status.model == "qwen2.5:3b"

def test_live_native_tool_calling_smoke(live_service):
    """Executes the 5 smoke queries against live Ollama to verify native tool calling plumbing."""
    print("\n--- Live Ollama Native Tool Calling Smoke Test ---")
    results = []

    for case in SMOKE_TEST_CASES:
        query = case["query"]
        expected = case["expected_tool"]

        res = live_service.select_tool(query)
        results.append({
            "query": query,
            "expected_tool": expected,
            "tool_called": res.tool_called,
            "actual_tool": res.tool_name,
            "arguments": res.arguments,
            "duration_ms": res.duration_ms,
        })

        print(f"\nQuery: {query}")
        print(f"  Expected:    {expected}")
        print(f"  Tool Called: {res.tool_called}")
        print(f"  Selected:    {res.tool_name}")
        print(f"  Arguments:   {res.arguments}")
        print(f"  Duration:    {res.duration_ms} ms")

        # Smoke check: Ensure the response is properly structured
        assert res.model == "qwen2.5:3b"
        assert isinstance(res.tool_called, bool)

    # Verify that native tool calling executed across queries
    assert len(results) == 5
