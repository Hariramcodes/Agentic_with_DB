from autogen import ConversableAgent
import logging
from utils.rag_utils import query_vector_db

logger = logging.getLogger(__name__)

def create_retrieval_agent(llm_config, agent_name):
    return ConversableAgent(
        name=f"{agent_name}_RetrievalAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="""You are a RetrievalAgent in Dell's technical support workflow. Your role is to fetch up to 5 relevant chunks from the vector DB for ChannelAgent, using 'VL.pdf' in the channel_agent table with cosine similarity search.

**Processing Instructions**:
1. Validate caller:
   - Format: "@ChannelAgent_RetrievalAgent: Fetch chunks for VL.pdf with query: <query>"
   - Log: "Received query from <agent_name>"
   - If invalid, respond: "@ChannelAgent: Invalid caller or format."
2. Extract query, region, and language from the prompt.
3. Query channel_agent table:
   - Use query_vector_db with pdf_name='VL.pdf', query, region, language.
   - Log: "Retrieved {len(chunks)} chunks for ChannelAgent from VL.pdf"
4. Respond:
   - Format: "@ChannelAgent: Retrieved chunks:\n<chunk1>\n<chunk2>\n..."
5. Errors:
   - Log: "Error querying database: <error>"
   - Respond: "@ChannelAgent: Error retrieving chunks: <error>"
"""
    )