"""Find the explicit-cache minimum token count for gemini-3.1-flash-lite on Vertex:
try creating caches of decreasing size; the smallest that succeeds ≈ the bar."""
import os, json
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("VERTEX_LOCATION", "global"))
from dotenv import load_dotenv; load_dotenv()
from google import genai
from google.genai import types
proj = json.load(open(os.path.expanduser("~/.config/gcloud/application_default_credentials.json"))).get("quota_project_id")
client = genai.Client(vertexai=True, project=proj, location=os.getenv("GOOGLE_CLOUD_LOCATION","global"))
MODEL = "gemini-3.1-flash-lite"
BASE = "The werewolf game proceeds through day and night phases; villagers vote, wolves deceive. "

for reps in [200, 120, 90, 70, 50, 40, 30]:
    content = BASE * reps
    try:
        cache = client.caches.create(
            model=MODEL,
            config=types.CreateCachedContentConfig(
                contents=[types.Content(role="user", parts=[types.Part(text=content)])], ttl="60s"),
        )
        tok = cache.usage_metadata.total_token_count
        client.caches.delete(name=cache.name)
        print(f"reps={reps:>3} tokens={tok:>6}  -> OK")
    except Exception as e:
        msg = str(e)
        # surface the min if the API states it
        print(f"reps={reps:>3} (~{len(content)//4} tok)  -> REJECTED: {msg[:160]}")
