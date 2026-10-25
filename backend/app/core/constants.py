"""Application constants for fixed tools and evaluation parameters."""

FIXED_TOOL_NAMES = [
    "search_web",
    "search_docs",
    "read_file",
    "write_file",
    "send_email",
    "create_calendar_event",
    "set_reminder",
    "get_weather",
    "calculator",
    "translate_text",
]

# Canonical complete label space in stable deterministic order
ALL_LABELS = FIXED_TOOL_NAMES + ["none"]

BASELINE_TOOL_DESCRIPTIONS = {
    "search_web": "Searches for information.",
    "search_docs": "Looks up information in documents.",
    "read_file": "Reads a file.",
    "write_file": "Writes data to a file.",
    "send_email": "Sends a message.",
    "create_calendar_event": "Adds an event.",
    "set_reminder": "Sets a reminder.",
    "get_weather": "Gets weather information.",
    "calculator": "Does math.",
    "translate_text": "Converts text.",
}

BENCHMARK_QUERY_COUNT = 50
TUNING_QUERY_COUNT = 35
HELD_OUT_QUERY_COUNT = 15
EVALUATION_TEMPERATURE = 0.0

# Optimization parameters
MAX_OPTIMIZATION_ROUNDS = 8
MAX_CONSECUTIVE_NON_IMPROVEMENTS = 2
MAX_DESCRIPTION_WORD_COUNT = 40

