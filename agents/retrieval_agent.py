from autogen import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from utils.rag_utils import pdf_to_txt, resolve_docs
import logging

logger = logging.getLogger(__name__)

AGENT_PDF_MAP = {
    "ChannelAgent": ["VL.pdf"],
    "EntitlementAnalyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
    "DamageAnalyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
    "DecisionOrchestrator": [],
    "RetrievalAgent": ["VL.pdf", "AccidentalDamage.pdf", "DELLSW.pdf", "BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]
}

class CustomRetrievalAgent(RetrieveUserProxyAgent):
    def __init__(self, name, llm_config):
        docs = []
        if name in AGENT_PDF_MAP:
            docs = resolve_docs(AGENT_PDF_MAP[name])
            logger.info(f"Mapped {len(docs)} PDFs for agent {name}: {docs}")
        else:
            logger.warning(f"No PDFs mapped for agent {name}, using default PDFs")
            docs = resolve_docs([
                "VL.pdf", "AccidentalDamage.pdf", "DELLSW.pdf",
                "BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"
            ])

        super().__init__(
            name=f"{name}_RetrievalAgent",
            retrieve_config={
                "docs_path": docs,
                "collection_name": f"dell_support_{name.lower()}",
                "vector_db": "pgvector",
                "db_config": {"connection_string": "postgresql://postgres:myragpw@localhost:5432/ragdb2"},
                "chunk_token_size": 512,
                "model": "all-MiniLM-L6-v2",
                "get_or_create": True,
                "k": 5
            },
            code_execution_config=False,
            llm_config=llm_config,
            system_message="""You are a custom RetrievalAgent in Dell's technical support workflow. Your role is to fetch exactly 5 relevant chunks from the vector DB for a given agent's query, based on the PDFs mapped to that agent.

**Role Description**:
- You fetch chunks from specific PDFs assigned to the calling agent.
- You validate the context of retrieved chunks to ensure relevance.
- You return raw chunks to the calling agent for summarization.

**Processing Instructions**:
1. Validate Caller:
   - Ensure the query comes from a valid agent (ChannelAgent, EntitlementAnalyzer, DamageAnalyzer).
   - Log: "Received query from <agent_name>"
2. Retrieve Chunks:
   - Use the provided query to fetch exactly 5 chunks from the vector DB.
   - Log: "Retrieved {len(chunks)} chunks for <agent_name> from {pdfs}"
3. Validate Context:
   - Check if chunks are relevant to the query.
   - Log: "Returning {len(valid_chunks)} chunks to <agent_name>"
"""
        )

    async def retrieve_chunks(self, query, agent_name):
        """Fetch exactly 5 chunks for the given agent and query."""
        try:
            if agent_name not in AGENT_PDF_MAP:
                logger.error(f"Invalid agent {agent_name}")
                return []

            logger.info(f"Received query from {agent_name}: {query}")
            chunks = await self.retrieve_docs(query=query)
            logger.info(f"Retrieved {len(chunks)} chunks for {agent_name} from {AGENT_PDF_MAP[agent_name]}")

            valid_chunks = [chunk for chunk in chunks if self._is_relevant(chunk, query, agent_name)]
            logger.info(f"Returning {len(valid_chunks)} valid chunks to {agent_name}")
            return valid_chunks[:5]
        except Exception as e:
            logger.error(f"Error retrieving chunks for {agent_name}: {e}")
            return []

    def _is_relevant(self, chunk, query, agent_name):
        """Validate chunk relevance."""
        keywords = {
            "ChannelAgent": ["upload", "image", "instructions"],
            "EntitlementAnalyzer": ["entitlement", "warranty", "accidental damage"],
            "DamageAnalyzer": ["damage", "biohazard", "monitor", "customer-induced"],
            "RetrievalAgent": ["upload", "entitlement", "damage", "warranty", "biohazard"]
        }
        agent_keywords = keywords.get(agent_name, [])
        return any(keyword.lower() in chunk.lower() for keyword in agent_keywords) or \
               any(keyword.lower() in query.lower() for keyword in agent_keywords)

def create_retrieval_agent(llm_config, agent_name):
    return CustomRetrievalAgent(name=agent_name, llm_config=llm_config)