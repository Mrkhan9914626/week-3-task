from agents import function_tool
from tavily import TavilyClient
from config import TAVILY_API_KEY


@function_tool
def web_search(query: str) -> str:
    """
    Search the web for current information.

    Args:
        query: The search query string to look up on the web.

    Returns:
        Formatted search results with titles, URLs, and content snippets.
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)

    try:
        results = client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
        )

        return _format_results(results)
    except Exception as e:
        return f"Search unavailable: {str(e)}"


def _format_results(results: dict) -> str:
    """Format Tavily search results into a structured string."""
    if not results.get("results"):
        return "No results found."

    formatted = []
    for i, result in enumerate(results["results"], 1):
        title = result.get("title", "No title")
        url = result.get("url", "")
        content = result.get("content", "No content available")

        formatted.append(f"{i}. {title}\n   URL: {url}\n   Content: {content}\n")

    return "\n".join(formatted)
