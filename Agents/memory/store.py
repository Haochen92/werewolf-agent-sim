"""The shared in-memory vector store + embeddings singletons (instantiated at import).

Module-level singletons used across the memory pipeline and the graphs. Isolated in their own
module so the import-time instantiation (creating the embeddings client + the indexed store) is
separated from the stateless retrieval accessors in Agents.memory.retrieval. Re-exported from
Agents.memory, so the common ``from Agents.memory import store`` call sites are unchanged.
"""

from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore

from Agents.llm_factory import (
    DEFAULT_EMBEDDING_DIMS,
    DEFAULT_EMBEDDING_MODEL,
    create_embeddings,
)

load_dotenv()

embeddings = create_embeddings(
    DEFAULT_EMBEDDING_MODEL,
    output_dimensionality=DEFAULT_EMBEDDING_DIMS,
)

store = InMemoryStore(
    index={
        "dims": DEFAULT_EMBEDDING_DIMS,
        "embed": embeddings,
        "fields": ["situation"],
    }
)
