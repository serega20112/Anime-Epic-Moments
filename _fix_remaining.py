"""Fix remaining infrastructure imports in application layer."""

import re

BASE = "."

files_to_fix = {
    "src/application/use_cases/anime/search_anime_by_description.py": [
        (r"from src\.infrastructure\.external\.huggingface_llm_client import \(\s*HuggingFaceLLMClient,\s*\)",
         "from src.domain.services.llm_client import LLMClientInterface as HuggingFaceLLMClient"),
    ],
    "src/application/services/watch_source_sync_service.py": [
        (r"from src\.infrastructure\.external\.watch_source_provider import \([^)]*\)",
         "from src.domain.services.watch_source_provider import WatchSourceProviderInterface as WatchSourceProvider"),
        (r"from src\.infrastructure\.cache\.ttl_cache import TTLCache",
         "from src.domain.services.ttl_cache import TTLCacheInterface as TTLCache"),
    ],
}

for filepath, patterns in files_to_fix.items():
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        if new_content != content:
            print(f"Fixed pattern in {filepath}")
            content = new_content
        else:
            print(f"Pattern not found in {filepath}: {pattern[:60]}...")
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved {filepath}")
    print()