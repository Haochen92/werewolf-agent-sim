"""Does EXPLICIT caching work for the game model on Vertex? Create a CachedContent
from a ~15k-token block, then invoke referencing it and check cache_read fires."""
import os
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("VERTEX_LOCATION", "global"))
from dotenv import load_dotenv
load_dotenv()
try:
    from google import genai
    from google.genai import types
except Exception as e:
    print("google-genai import failed:", e); raise SystemExit

import json
proj = json.load(open(os.path.expanduser("~/.config/gcloud/application_default_credentials.json"))).get("quota_project_id")
client = genai.Client(vertexai=True, project=proj, location=os.getenv("GOOGLE_CLOUD_LOCATION","global"))
MODEL = "gemini-3.1-flash-lite"
BASE = ("The werewolf game proceeds through alternating day and night phases where "
        "villagers debate, accuse, and vote while hidden wolves deceive the town. ")
content = BASE * 600  # ~15k tokens

for min_try, ttl in [(content, "120s")]:
    try:
        cache = client.caches.create(
            model=MODEL,
            config=types.CreateCachedContentConfig(
                contents=[types.Content(role="user", parts=[types.Part(text=content)])],
                ttl=ttl,
            ),
        )
        print("cache created:", cache.name, "| cached_token_count=", getattr(cache.usage_metadata, "total_token_count", "?"))
        resp = client.models.generate_content(
            model=MODEL,
            contents="Reply with only: x",
            config=types.GenerateContentConfig(cached_content=cache.name),
        )
        um = resp.usage_metadata
        print("cached_content_token_count =", um.cached_content_token_count)
        print("prompt_token_count =", um.prompt_token_count)
        client.caches.delete(name=cache.name)
        print("cache deleted")
    except Exception as e:
        print("EXPLICIT CACHE ERROR:", type(e).__name__, str(e)[:300])
