import os
import sys
import django
import logging

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

print("\n" + "="*60)
print("ADVANCED RAG ARCHITECTURE TEST")
print("="*60)

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

    print("\n" + "="*60)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*60)
    print(f"Complexity Score: {result['complexity']} / 5.0")
    print(f"Used Multi-Query (Parallel): {result['metadata']['used_multi_query']}")
    print(f"Query Variations Generated:")
    for v in result['metadata']['query_variations']:
        print(f" - {v}")
    print(f"Retrieved Documents: {len(result['retrieved_docs'])}")
    
except Exception as e:
    print(f"Error during execution: {e}")
