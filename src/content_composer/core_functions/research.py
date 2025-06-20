"""Research and search functions."""

import asyncio
import os
from typing import Any, Dict

import requests
from loguru import logger


async def research_news_stub(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    A stub function that simulates researching news for a given topic.
    It expects 'topic' in the input dictionary.
    """
    topic = inputs.get("topic")
    logger.info(f"[Core Function] research_news_stub called with topic: {topic}")
    if not topic:
        return {"error": "Topic not provided for research_news_stub"}

    # Simulate fetching news
    return {
        "summary": f"Research summary for '{topic}': AI continues to evolve rapidly, impacting various sectors. Recent developments include new large language models and ethical discussions.",
        "articles": [
            {
                "title": f"AI Breakthroughs in {topic} Announced",
                "source": "Tech News Today",
                "url": f"http://example.com/news/{topic.lower().replace(' ', '-')}-breakthroughs",
            },
            {
                "title": f"The Ethical Implications of AI in {topic}",
                "source": "Ethics in Technology Quarterly",
                "url": f"http://example.com/news/{topic.lower().replace(' ', '-')}-ethics",
            },
        ],
        "related_keywords": [
            "machine learning",
            "deep learning",
            "neural networks",
            topic.lower(),
        ],
    }


async def perplexity_search_task(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs a web search using Perplexity's API based on inputs.
    Expected inputs: 'search_query' (str), 'recency' (str, optional), 'mode' (str, optional).
    """
    search_query = inputs.get("search_query")
    recency = inputs.get("recency")  # Optional
    mode = inputs.get("mode")  # Optional, defaults to 'fast' in underlying logic

    logger.info(
        f"[Core Function] perplexity_search_task called with query: '{search_query}', recency: '{recency}', mode: '{mode}'"
    )

    if not search_query:
        return {"error": "'search_query' not provided for perplexity_search_task"}

    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("PERPLEXITY_API_KEY not found in environment variables.")
        return {"error": "PERPLEXITY_API_KEY not set."}

    url = "https://api.perplexity.ai/chat/completions"
    pplx_model = "sonar-reasoning-pro" if mode == "expert" else "sonar-pro"

    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant.",  # Simplified system prompt for now, can be expanded
        },
        {
            "role": "user",
            "content": search_query,
        },
    ]
    payload = {
        "model": pplx_model,
        "messages": messages,
        "max_tokens": 3500,  # Made integer
        "temperature": 0.7,
        "top_p": 0.9,
        "return_citations": True,
        "return_images": False,
        "return_related_questions": False,
    }
    if recency:
        payload["search_recency_filter"] = recency

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        # Run the synchronous requests call in a separate thread
        response = await asyncio.to_thread(
            requests.post, url, json=payload, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        response_json = response.json()
        content = (
            response_json.get("choices", [{}])[0].get("message", {}).get("content")
        )

        if content is None:
            logger.error(
                f"Perplexity API response did not contain expected content structure. Response: {response_json}"
            )
            return {
                "error": "Perplexity API query failed to return content.",
                "details": response_json,
            }

        logger.info(f"Perplexity search successful for query: '{search_query}'")
        return {"content": content, "citations": response_json.get("citations", [])}

    except requests.exceptions.HTTPError as http_err:
        logger.error(
            f"HTTP error occurred during Perplexity API call: {http_err} - Response: {http_err.response.text}"
        )
        return {
            "error": f"Perplexity API HTTP error: {http_err.response.status_code}",
            "details": http_err.response.text,
        }
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred during Perplexity API call: {req_err}")
        return {"error": f"Perplexity API request error: {req_err}"}
    except Exception as e:
        logger.exception(f"An unexpected error occurred in perplexity_search_task: {e}")
        return {"error": f"Unexpected error in perplexity_search_task: {str(e)}"}