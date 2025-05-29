from __future__ import annotations
import json
from duckduckgo_search import DDGS
import logging
ddgs = DDGS()

def web_search(query: str, num_results: int = 8) -> str:
    """Useful for general internet search queries."""
    
    # Set the root logger's level to CRITICAL to prevent logs from being printed to the terminal
    logging.basicConfig(filename='selenium_logs.log', level=logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    logging.getLogger("selenium").setLevel(logging.CRITICAL)
    logging.getLogger().setLevel(logging.CRITICAL)
    
    print("Searching with query {0}...".format(query))
    search_results = []
    if not query:
        return json.dumps(search_results)

    results = ddgs.text(query)
    if not results:
        return json.dumps(search_results)

    total_added = 0
    for j in results:
        search_results.append(j)
        total_added += 1
        if total_added >= num_results:
            break

    return json.dumps(search_results, ensure_ascii=False, indent=4)
