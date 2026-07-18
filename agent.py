from openai import AsyncOpenAI
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    set_tracing_export_api_key,
)

from config import GEMINI_API_KEY, OPENAI_API_KEY
from tools import web_search, calculator, read_file, execute_code

# Use the OpenAI API key specifically for tracing
# Without this, tracing won't work because we use a custom client for Gemini
if OPENAI_API_KEY:
    set_tracing_export_api_key(OPENAI_API_KEY)

# Configure Gemini via OpenAI-compatible endpoint
_gemini_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

_gemini_model = OpenAIChatCompletionsModel(
    model="gemini-3.1-flash-lite-preview",
    openai_client=_gemini_client,
)

# System prompt instructing the agent on tool usage
SYSTEM_PROMPT = """You are a powerful multi-tool AI assistant. You have access to four tools:

1. **web_search(query)**: Search the web for current information. Use for facts, news, weather, or anything you don't already know.
2. **calculator(expression)**: Evaluate mathematical expressions like "2 + 3 * 4" or "sqrt(144)". Supports +, -, *, /, pow, sqrt, trig functions, log, and constants pi/e.
3. **read_file(file_path, start_line, end_line)**: Read the contents of a file from the project directory. Optionally specify a line range.
4. **execute_code(code)**: Execute Python code in a sandboxed environment and get the output. Available modules: math, json, random, datetime, collections, itertools, statistics, string, re.

Guidelines:
- Think step-by-step before choosing a tool.
- You can chain multiple tools together to solve complex tasks.
- When searching the web, cite sources by title and URL in your final answer.
- When reading files, mention which file you read and what you found.
- When executing code, explain what the code does and the result.
- If a tool returns an error, try a different approach or explain the limitation.
- If you need to do multiple steps, do them one at a time, using the result of each step to inform the next.
"""

_agent = Agent(
    name="MultiToolAgent",
    instructions=SYSTEM_PROMPT,
    tools=[web_search, calculator, read_file, execute_code],
    model=_gemini_model,
)


async def run_agent(query: str, max_turns: int = 15) -> str:
    """
    Run the multi-tool agent with a query and return the final answer.

    Args:
        query: The user's question or request.
        max_turns: Maximum number of LLM-tool cycles before stopping.

    Returns:
        The agent's final response as a string.
    """
    result = await Runner.run(
        _agent,
        input=query,
        max_turns=max_turns,
    )
    return result.final_output


async def run_agent_streamed(query: str, max_turns: int = 15):
    """
    Run the multi-tool agent with streaming, yielding events.

    Args:
        query: The user's question or request.
        max_turns: Maximum number of LLM-tool cycles before stopping.

    Yields:
        Dict events: {"type": "tool_call"|"tool_output"|"final_output", ...}
    """
    from agents import ItemHelpers

    result = Runner.run_streamed(
        _agent,
        input=query,
        max_turns=max_turns,
    )

    # Track call_id -> tool_name across events
    _tool_call_map: dict[str, str] = {}

    async for event in result.stream_events():
        # Ignore raw token-level response deltas
        if event.type == "raw_response_event":
            continue

        # Agent handoff (not used here but handled gracefully)
        elif event.type == "agent_updated_stream_event":
            yield {"type": "agent_update", "agent": event.new_agent.name}
            continue

        # Rich item events
        elif event.type == "run_item_stream_event":
            item = event.item

            if item.type == "tool_call_item":
                raw = item.raw_item
                name = getattr(raw, "name", "unknown")
                call_id = item.call_id or ""
                if call_id:
                    _tool_call_map[call_id] = name
                yield {
                    "type": "tool_call",
                    "tool": name,
                    "arguments": getattr(raw, "arguments", "{}"),
                }

            elif item.type == "tool_call_output_item":
                call_id = item.call_id or ""
                tool_name = _tool_call_map.get(call_id, "unknown")
                yield {
                    "type": "tool_output",
                    "tool": tool_name,
                    "output": str(item.output) if item.output else "",
                }

            elif item.type == "message_output_item":
                text = ItemHelpers.text_message_output(item)
                if text.strip():
                    yield {
                        "type": "final_output",
                        "output": text,
                    }

    # After streaming completes, get the final result
    final = result.final_output
    yield {
        "type": "final_output",
        "output": final,
    }


async def test_tools():
    """Test each tool individually."""
    from agents import Runner

    print("=" * 60)
    print("TESTING TOOLS")
    print("=" * 60)

    # Test calculator
    print("\n--- Calculator ---")
    calc_agent = Agent(
        name="CalcTest",
        instructions="Use the calculator tool.",
        tools=[calculator],
        model=_gemini_model,
    )
    r = await Runner.run(calc_agent, "What is 2^10 + 5*3?")
    print(r.final_output)

    # Test web search
    print("\n--- Web Search ---")
    search_agent = Agent(
        name="SearchTest",
        instructions="Use the web search tool.",
        tools=[web_search],
        model=_gemini_model,
    )
    r = await Runner.run(search_agent, "What is the capital of France?")
    print(r.final_output)

    # Test file reader (read this file itself)
    print("\n--- File Reader ---")
    file_agent = Agent(
        name="FileTest",
        instructions="Use the read_file tool.",
        tools=[read_file],
        model=_gemini_model,
    )
    r = await Runner.run(file_agent, "Read the config.py file")
    print(r.final_output)

    # Test code executor
    print("\n--- Code Executor ---")
    code_agent = Agent(
        name="CodeTest",
        instructions="Use the execute_code tool.",
        tools=[execute_code],
        model=_gemini_model,
    )
    r = await Runner.run(code_agent, "Write and execute Python code to print the first 10 Fibonacci numbers")
    print(r.final_output)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools())
