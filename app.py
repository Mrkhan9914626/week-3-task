import asyncio
import json
import uuid

import streamlit as st

from agent import run_agent, run_agent_streamed

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Multi-Tool Agent",
    page_icon="🛠️",
    layout="wide",
)

st.title("🛠️ Multi-Tool Agent")
st.caption("Powered by Gemini via OpenAI Agents SDK + Tavily Search")

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Available Tools")

    st.markdown("""
    | Tool | Description |
    |------|-------------|
    | 🌐 **Web Search** | Search the web for current info |
    | 🧮 **Calculator** | Safe math expression evaluator |
    | 📄 **File Reader** | Read files from the project |
    | 🐍 **Code Executor** | Run Python code in sandbox |
    """)

    st.divider()

    st.subheader("Controls")
    if st.button("Clear Conversation", type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.subheader("Display Mode")
    mode = st.radio(
        "Mode",
        options=["Detailed", "Simple"],
        index=0,
        help="Detailed shows tool reasoning steps; Simple shows only the final answer",
    )
    st.session_state.mode = mode

    st.divider()
    st.caption(f"Thread ID: {st.session_state.get('thread_id', '—')[:8]}...")

    st.divider()
    st.subheader("About")
    st.markdown("""
    This agent can:
    - Search the web for current information
    - Calculate math expressions
    - Read files from the project
    - Execute Python code in a sandbox

    Tasks that require multiple steps are handled in sequence.
    """)

# ── Async Helpers ──────────────────────────────────────────────────────────────


def _run_async(coro):
    """Run an async coroutine to completion and return its result."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # Already inside a running loop — spawn a new one in a thread
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


def _run_async_gen(async_gen):
    """Exhaust an async generator and return all events as a list."""
    async def _collect():
        events = []
        async for event in async_gen:
            events.append(event)
        return events
    return _run_async(_collect())


# ── Backend Handlers ───────────────────────────────────────────────────────────


def _handle_simple_response(prompt: str):
    """Run the agent and show just the final answer."""
    placeholder = st.empty()
    with placeholder, st.spinner("Thinking..."):
        try:
            output = _run_async(run_agent(prompt, max_turns=15))
        except Exception as e:
            st.error(f"Error running agent: {str(e)}")
            return

    if not output or output.strip() == "":
        placeholder.warning("No answer was generated.")
        return

    placeholder.markdown(output)
    st.session_state.messages.append({"role": "assistant", "content": output})


def _handle_detailed_response(prompt: str):
    """Run the agent stream, collect events, and display reasoning + answer."""
    reasoning_container = st.container()
    answer_container = st.container()

    with reasoning_container:
        st.caption("💭 Reasoning Steps")

    with st.spinner("Processing..."):
        events = _run_async_gen(run_agent_streamed(prompt, max_turns=15))

    if not events:
        with reasoning_container:
            st.warning("No events received from the agent.")
        return

    step_number = 0
    final_output_text = None
    error_occurred = False

    for event in events:
        event_type = event.get("type")

        if event_type == "tool_call":
            step_number += 1
            tool = event.get("tool", "unknown")
            args_raw = event.get("arguments", {})

            if isinstance(args_raw, str):
                try:
                    args_display = json.loads(args_raw)
                except json.JSONDecodeError:
                    args_display = args_raw
            else:
                args_display = args_raw

            with reasoning_container:
                with st.expander(
                    f"🔧 Step {step_number}: Action — {tool}",
                    expanded=True,
                ):
                    st.json(args_display)

        elif event_type == "tool_output":
            output = event.get("output", "")
            tool = event.get("tool", "unknown")

            max_display = 500
            display_text = (
                output[:max_display] + "..."
                if len(output) > max_display
                else output
            )

            with reasoning_container:
                with st.expander(
                    f"📊 Observation ({tool})",
                    expanded=False,
                ):
                    st.text(display_text)

        elif event_type == "final_output":
            final_output_text = event.get("output", "")
            if final_output_text:
                with answer_container:
                    st.divider()
                    st.markdown(final_output_text)

        elif event_type == "error":
            error_occurred = True
            with reasoning_container:
                st.error(f"Error: {event.get('detail', 'Unknown error')}")

        elif event_type == "agent_update":
            with reasoning_container:
                st.caption(f"→ Switched to: {event.get('agent', '?')}")

    if final_output_text:
        st.session_state.messages.append(
            {"role": "assistant", "content": final_output_text}
        )
    elif not error_occurred:
        with answer_container:
            st.warning("No final answer was generated.")


# ── Session State ──────────────────────────────────────────────────────────────

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "Detailed"

# ── Display Chat History ───────────────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Chat Input ─────────────────────────────────────────────────────────────────

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.mode == "Detailed":
            _handle_detailed_response(prompt)
        else:
            _handle_simple_response(prompt)
