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





