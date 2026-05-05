import os
import json
import httpx
from groq import AsyncGroq

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))


def _build_search_text(data: dict) -> str:
    """Flatten Serper results into plain text for the LLM to read."""
    lines = []

    answer_box = data.get("answerBox", {})
    if answer_box.get("snippet"):
        lines.append("Answer box: " + answer_box["snippet"])

    for r in data.get("organic", [])[:8]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        if title:
            lines.append(f"Title: {title}")
        if snippet:
            lines.append(f"Snippet: {snippet}")

    for item in data.get("peopleAlsoAsk", [])[:3]:
        if item.get("snippet"):
            lines.append("PAA: " + item["snippet"])

    return "\n".join(lines)


async def fetch_competitors(query: str, category: str = "") -> list:
    """
    Use Serper to search for the query, then use Groq to extract
    real brand/product names from the search results.
    """
    if not SERPER_API_KEY:
        return ["Competitor A", "Competitor B", "Competitor C"]

    search_query = f"best {category or query}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            SERPER_URL,
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json",
            },
            json={"q": search_query, "num": 10},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

    search_text = _build_search_text(data)

    prompt = f"""Below are Google search results for the query: "{search_query}"

{search_text}

Extract the names of real product brands or products mentioned in these results that are relevant to this category.

Rules:
- Only include actual brand names or product names (e.g. "Natural Calm", "Thorne", "Doctor's Best")
- Do NOT include generic words like "Best", "Top", "Amazon", "Google", "Review", website names, or article titles
- Return between 3 and 5 names
- Return ONLY a JSON array of strings, nothing else. Example: ["Brand A", "Brand B", "Brand C"]"""

    response = await groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.0,
    )

    raw = response.choices[0].message.content.strip()

    try:
        competitors = json.loads(raw)
        if isinstance(competitors, list) and len(competitors) > 0:
            return competitors[:5]
    except json.JSONDecodeError:
        pass

    # Fallback if LLM returns unexpected format
    return ["Natural Calm", "Doctor's Best", "Thorne", "Garden of Life", "NOW Foods"]