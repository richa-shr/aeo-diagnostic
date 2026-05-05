import os
import asyncio
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

ENGINES = [
    {
        "name": "Llama 3.3 70b",
        "model": "llama-3.3-70b-versatile",
        "description": "Large, highly capable model — represents premium AI assistants",
    },
    {
        "name": "Llama 4 Scout 17b",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "description": "Mixture-of-experts architecture — different reasoning patterns",
    },
    {
        "name": "Llama 3.1 8b",
        "model": "llama-3.1-8b-instant",
        "description": "Smaller, faster model — represents lightweight AI assistants",
    },
]

SHOPPER_PROMPT = """You are a helpful AI assistant. A shopper has asked you a product question.

Shopper query: "{query}"

The following products exist in this space: {products_list}

Product details for "{product_name}": {product_description}

Answer the shopper's question naturally and helpfully. Recommend products by name where relevant. Be honest about what you'd actually recommend and why. Keep your response under 200 words."""


async def query_engine(engine: dict, query: str, product_name: str, product_description: str, competitors: list) -> dict:
    all_products = [product_name] + [c for c in competitors if c != product_name]
    products_list = ", ".join(all_products)

    prompt = SHOPPER_PROMPT.format(
        query=query,
        products_list=products_list,
        product_name=product_name,
        product_description=product_description or "No additional details provided.",
    )

    response = await client.chat.completions.create(
        model=engine["model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )

    text = response.choices[0].message.content.strip()

    # Detect if product is mentioned
    mentioned = product_name.lower() in text.lower()

    # Rough rank detection: find position among products mentioned
    rank = None
    text_lower = text.lower()
    mentioned_products = []
    for p in all_products:
        if p.lower() in text_lower:
            pos = text_lower.find(p.lower())
            mentioned_products.append((pos, p))
    mentioned_products.sort()

    if mentioned_products:
        for i, (_, name) in enumerate(mentioned_products):
            if name.lower() == product_name.lower():
                rank = i + 1
                break

    return {
        "engine": engine["name"],
        "model_used": engine["model"],
        "response": text,
        "mentioned": mentioned,
        "rank": rank,
    }


async def run_all_engines(query: str, product_name: str, product_description: str, competitors: list) -> list:
    tasks = [
        query_engine(engine, query, product_name, product_description, competitors)
        for engine in ENGINES
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any individual engine failures gracefully
    clean = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            clean.append({
                "engine": ENGINES[i]["name"],
                "model_used": ENGINES[i]["model"],
                "response": "Engine unavailable.",
                "mentioned": False,
                "rank": None,
            })
        else:
            clean.append(r)
    return clean