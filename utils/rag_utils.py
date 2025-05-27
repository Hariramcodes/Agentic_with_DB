# import os
# from pathlib import Path
# import PyPDF2
# from autogen import AssistantAgent
# from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
# from config.llm_config import *

# def pdf_to_txt(pdf_path: Path) -> Path:
#     txt_path = pdf_path.with_suffix(".txt")
#     if txt_path.exists():
#         return txt_path
#     text = "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(pdf_path).pages)
#     txt_path.write_text(text, encoding="utf-8")
#     return txt_path

# def resolve_docs(pdfs):
#     return [str(pdf_to_txt(Path("docs") / p)) for p in pdfs]

# def build_rag_pair(name: str, collection: str):
#     docs = resolve_docs(DOC_MAP[name])
    
#     assistant = AssistantAgent(
#         name=f"{name}_rag_assistant",
#         system_message=f"""You are the {name} RAG specialist. Return verbatim chunks only.""",
#         llm_config={
#             "config_list": CONFIG_LIST,
#             "temperature": 0.0,
#             "timeout": 600,
#         },
#     )

#     proxy = RetrieveUserProxyAgent(
#         name=f"{name}_rag_proxy",
#         retrieve_config={
#             "docs_path": docs,
#             "collection_name": collection,
#             "vector_db": "pgvector",
#             "db_config": {"connection_string": DB_CONN},
#             "chunk_token_size": CHUNK_TOKENS,
#             "model": EMBED_MODEL,
#             "get_or_create": True,
#         },
#         code_execution_config=False,
#     )
#     return proxy, assistant









































































import os
from pathlib import Path
import PyPDF2
import logging
import asyncpg
from typing import Optional

logger = logging.getLogger(__name__)

DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"
CHUNK_TOKENS = 200
EMBED_MODEL = "all-MiniLM-L6-v2"
DOC_MAP = {
    "ChannelAgent": ["VL.pdf"],
    "EntitlementAnalyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
    "DamageAnalyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
    "DecisionOrchestrator": []
}

def pdf_to_txt(pdf_path: Path) -> Path:
    """Convert PDF to text file for vector DB ingestion."""
    txt_path = pdf_path.with_suffix(".txt")
    if txt_path.exists():
        return txt_path
    text = "".join(page.extract_text() or "" for page in PyPDF2.PdfReader(pdf_path).pages)
    txt_path.write_text(text, encoding="utf-8")
    logger.info(f"Converted {pdf_path} to {txt_path}")
    return txt_path

def resolve_docs(pdfs):
    """Resolve PDF paths and convert to text."""
    return [str(pdf_to_txt(Path("docs") / p)) for p in pdfs]

async def query_vector_db(pdf_name: str, query: str, k: int = 1, retrieval_agent: Optional[object] = None) -> list:
    """Query vector DB for chunks relevant to the query."""
    try:
        if retrieval_agent:
            chunks = await retrieval_agent.retrieve_chunks(query, pdf_name.split(".")[0])
            logger.info(f"Retrieved {len(chunks)} chunks for {pdf_name} via RetrievalAgent")
            return chunks[:k]

        pdf_path = Path("docs") / pdf_name
        txt_path = pdf_to_txt(pdf_path)

        conn = await asyncpg.connect(DB_CONN)
        rows = await conn.fetch(
            """
            SELECT content
            FROM documents
            WHERE pdf_name = $1
            ORDER BY embedding <=> (SELECT embedding FROM embeddings WHERE text = $2)
            LIMIT $3
            """,
            pdf_name, query, k
        )
        await conn.close()
        chunks = [row['content'] for row in rows]
        logger.info(f"Retrieved {len(chunks)} chunks for {pdf_name} with query: {query}")
        return chunks
    except Exception as e:
        logger.error(f"Error querying vector DB for {pdf_name}: {e}")
        return []