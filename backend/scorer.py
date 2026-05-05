import os
import json
import re
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))


def compute_basic_scores(product_name: str, engine_responses: list) -> dict:
    """Compute raw scores from engine responses before LLM analysis."""
    total = len(engine_responses)
    mentioned_count = sum(1 for r in engine_responses if r.get("mentioned"))
    mention_rate = round((mentioned_count / total) * 100) if total else 0

    ranks = [r.get("rank") for r in engine_responses if r.get("rank") is not None]
    avg_rank = round(sum(ranks) / len(ranks)) if ranks else None

    return {
        "mention_rate": mention_rate,
        "mentioned_count": mentioned_count,
        "total_engines": total,
        "avg_rank": avg_rank,
    }


def grade_from_score(score: int) -> str:
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 45:
        return "C"
    else:
        return "F"


async def generate_report(product_name: str, query: str, competitors: list, engine_responses: list) -> dict:
    basic = compute_basic_scores(product_name, engine_responses)

    # Build a summary of engine responses for the LLM analyst
    responses_summary = ""
    for r in engine_responses:
        responses_summary += f"\n\n--- {r['engine']} ---\n"
        responses_summary += f"Mentioned {product_name}: {'YES' if r['mentioned'] else 'NO'}\n"
        responses_summary += f"Rank position: {r['rank'] or 'Not ranked'}\n"
        responses_summary += f"Response: {r['response']}"

    competitors_str = ", ".join(competitors)

    prompt = f"""You are an AEO (Answer Engine Optimization) analyst. Analyze how well a product performs when AI engines respond to shopper queries.

PRODUCT: {product_name}
SHOPPER QUERY: "{query}"
COMPETITORS: {competitors_str}

MENTION RATE: {basic['mention_rate']}% ({basic['mentioned_count']} of {basic['total_engines']} engines mentioned it)
AVERAGE RANK: {basic['avg_rank'] or 'Not ranked in any engine'}

AI ENGINE RESPONSES:
{responses_summary}

Based on this data, generate a detailed AEO report card. Return ONLY valid JSON, no markdown, no explanation:

{{
  "overall_score": <integer 0-100>,
  "grade": "<A/B/C/F>",
  "mention_rate": {basic['mention_rate']},
  "avg_rank": <integer or null>,
  "visibility_score": <integer 0-100, how visible is the product across engines>,
  "trust_score": <integer 0-100, how credibly is it described when mentioned>,
  "competitor_ranking": [
    <array of competitor names + the product, ordered best to worst AEO rank, as strings>
  ],
  "engine_breakdown": [
    {{"engine": "<name>", "mentioned": <true/false>, "rank": <int or null>, "score": <0-100>}}
  ],
  "rank_explanation": "<2-3 sentences explaining why this product ranks where it does based on the AI responses>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "fixes": [
    {{"priority": "high", "title": "<fix title>", "detail": "<one sentence on how to implement>"}},
    {{"priority": "high", "title": "<fix title>", "detail": "<one sentence on how to implement>"}},
    {{"priority": "med", "title": "<fix title>", "detail": "<one sentence on how to implement>"}},
    {{"priority": "low", "title": "<fix title>", "detail": "<one sentence on how to implement>"}}
  ]
}}"""

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: construct report from basic scores
        report = {
            "overall_score": basic["mention_rate"],
            "grade": grade_from_score(basic["mention_rate"]),
            "mention_rate": basic["mention_rate"],
            "avg_rank": basic["avg_rank"],
            "visibility_score": basic["mention_rate"],
            "trust_score": 50,
            "competitor_ranking": [product_name] + competitors,
            "engine_breakdown": [
                {"engine": r["engine"], "mentioned": r["mentioned"], "rank": r["rank"], "score": 70 if r["mentioned"] else 20}
                for r in engine_responses
            ],
            "rank_explanation": "Analysis could not be fully parsed. Based on raw mention data.",
            "strengths": ["Product was recognized by at least one engine"],
            "fixes": [
                {"priority": "high", "title": "Add more specific product details", "detail": "Include dosage, form, and certifications in your product description."},
                {"priority": "med", "title": "Build review presence", "detail": "Increase reviews on major platforms so AI engines encounter your product more frequently."},
            ],
        }

    # Always inject raw engine responses for frontend display
    report["engine_responses"] = engine_responses
    report["competitors_used"] = competitors

    return report