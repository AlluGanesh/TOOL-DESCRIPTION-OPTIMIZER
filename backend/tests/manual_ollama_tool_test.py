"""Manual diagnostic script to test native tool-calling with qwen2.5:3b via Ollama.

This script is purely diagnostic and does not run evaluation, calculate accuracy,
or modify any benchmark files or tool definitions.
"""

import json
import os
import sys
import time
import importlib.metadata
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import ollama
from backend.app.core.config import OLLAMA_HOST, OLLAMA_MODEL, TOOLS_FILE
from backend.app.services.tool_service import load_canonical_tools, tools_to_ollama_format

def run_diagnostic():
    print("=" * 60)
    print("OLLAMA NATIVE TOOL CALLING DIAGNOSTIC")
    print("=" * 60)

    # 1. Environment & Version Info
    print(f"Configured Host:       {OLLAMA_HOST}")
    print(f"Configured Model:      {OLLAMA_MODEL}")
    try:
        pkg_version = importlib.metadata.version("ollama")
    except Exception:
        pkg_version = "unknown"
    print(f"Python ollama package: {pkg_version}")

    # Check CLI version if available
    cli_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
    if cli_path.exists():
        import subprocess
        try:
            res = subprocess.run([str(cli_path), "--version"], capture_output=True, text=True, timeout=5)
            print(f"Ollama binary version: {res.stdout.strip()}")
        except Exception as e:
            print(f"Ollama binary check:  {e}")
    else:
        print("Ollama binary path:    Not found in standard LocalAppData path")

    print("-" * 60)

    # 2. Load Tools
    print(f"Loading canonical tools from: {TOOLS_FILE}")
    tools = load_canonical_tools(TOOLS_FILE)
    print(f"Loaded {len(tools)} canonical tools.")
    formatted_tools = tools_to_ollama_format(tools)

    # 3. Setup Client with explicit 60-second timeout
    client = ollama.Client(host=OLLAMA_HOST, timeout=60.0)

    # 4. Define Query
    test_query = "What is 25 multiplied by 16?"
    print(f"Test Query:            \"{test_query}\"")
    print("Sending native tool calling request (timeout=60s, temperature=0.0)...")

    start_time = time.perf_counter()
    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": test_query}],
            tools=formatted_tools,
            options={"temperature": 0.0},
        )
        elapsed_seconds = time.perf_counter() - start_time
    except Exception as exc:
        elapsed_seconds = time.perf_counter() - start_time
        print("\n" + "!" * 60)
        print(f"REQUEST FAILED after {elapsed_seconds:.2f} seconds!")
        print(f"Exception Type: {type(exc).__name__}")
        print(f"Exception Message: {exc}")
        print("!" * 60)
        import traceback
        traceback.print_exc()
        return

    # 5. Analyze Response
    print("\n" + "=" * 60)
    print("DIAGNOSTIC RESULTS")
    print("=" * 60)
    print(f"Elapsed Time:          {elapsed_seconds:.2f} seconds ({elapsed_seconds * 1000:.1f} ms)")
    print(f"Model:                 {response.model}")

    msg = getattr(response, "message", None)
    content = getattr(msg, "content", "") if msg else ""
    tool_calls = getattr(msg, "tool_calls", None) if msg else None

    # Performance breakdown from Ollama if present
    if hasattr(response, "total_duration") and response.total_duration:
        total_ms = response.total_duration / 1e6
        load_ms = (response.load_duration or 0) / 1e6
        prompt_ms = (response.prompt_eval_duration or 0) / 1e6
        eval_ms = (response.eval_duration or 0) / 1e6
        print(f"Ollama Server Timing:  Total={total_ms:.1f}ms (Load={load_ms:.1f}ms, PromptEval={prompt_ms:.1f}ms, Eval={eval_ms:.1f}ms)")

    has_tool_call = bool(tool_calls and len(tool_calls) > 0)
    print(f"Tool Call Returned:    {has_tool_call}")

    if has_tool_call:
        first_call = tool_calls[0]
        func = getattr(first_call, "function", None)
        tool_name = getattr(func, "name", None) if func else None
        arguments = getattr(func, "arguments", {}) if func else {}
        print(f"Selected Tool:         {tool_name}")
        print(f"Selected Arguments:    {json.dumps(arguments)}")
        print("\nDiagnosis Category:    SUCCESSFULLY RETURNING A NATIVE TOOL CALL")
    elif content.strip():
        print(f"Normal Text Response:  \"{content.strip()}\"")
        print("\nDiagnosis Category:    RETURNING A NORMAL TEXT RESPONSE (No tool called)")
    else:
        print("Response was empty without tool call or text content.")
        print("\nDiagnosis Category:    EMPTY RESPONSE")

    print("=" * 60)

if __name__ == "__main__":
    run_diagnostic()
