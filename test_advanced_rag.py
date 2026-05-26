import logging
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'room_booking_system.settings')
django.setup()

# Enable logging to see the pipeline in action
logging.basicConfig(level=logging.INFO, format='%(message)s')

from ai.agentic_rag import AgenticRAG
from ai.vector_store import get_vector_store


class DummyLLM:
    """Mock LLM to demonstrate the LLM Query Rewriter safely."""
    def generate(self, prompt):
        return (
            "what is the cancellation policy for bookings?\n"
            "how to cancel a reservation?\n"
            "cancellation rules for rooms\n"
        )


try:
    vs = get_vector_store()

    rag = AgenticRAG(
        vector_store=vs,
        llm_client=DummyLLM(),
        enable_multi_query=True,
        enable_self_rag=False, # disabled to focus on the retrieval architecture
        enable_reranking=True
    )

    # A complex query to trigger complexity score >= 2.5 and multi-query
    query = "I want to reserve a room for a conference with 50 people tomorrow morning. What is the policy for cancellation?"

    result = rag.process_query(query, top_k=3)

    for _v in result['metadata']['query_variations']:
        pass

except Exception:
    pass
