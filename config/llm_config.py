# # Ollama-served model configuration
# config_list = [
#     {
#         "model": "llama3.1:8b",
#         "base_url": "http://localhost:11434/v1",
#         "api_key": "ollama",
#         "price": [0.0, 0.0]  # Silences the pricing warning
#     }
# ]

# # LLM configuration with temperature and top_p settings
# llm_config = {
#     "config_list": config_list,
#     "cache_seed": None,
#     "temperature": 0.0,
#     "top_p": 0.0,
#     "timeout": 500,

# }




















# # Global configurations
# LLM_BASE_URL = "http://localhost:11434/v1"
# DB_CONN = "postgresql://postgres:myragpw@localhost:5434/ragdb2"
# EMBED_MODEL = "nomic-embed-text:latest"
# CHUNK_TOKENS = 200
# TOP_K = 1

# CONFIG_LIST = [{
#     "model": "llama3.1:8b",
#     "base_url": LLM_BASE_URL,
#     "api_key": "ollama",
#     "price": [0.0, 0.0],
# }]

# LLM_CONFIG = {
#     "config_list": CONFIG_LIST,
#     "cache_seed": None,
#     "temperature": 0.0,
#     "top_p": 0.0,
#     "timeout": 500,
# }

# DOC_MAP = {
#     "damage_analyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
#     "entitlement_analyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
#     "channel_agent": ["VL.pdf"],
# }







# config/llm_config.py
from autogen import config_list_from_json

# Ollama configuration
CONFIG_LIST = [
    {
        "model": "llama3.1:8b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

# LLM configuration
llm_config = {
    "config_list": CONFIG_LIST,
    "temperature": 0.0,
    "timeout": 600,
}

# Database configuration
DB_CONFIG = {
    "connection_string": "postgresql://postgres:myragpw@localhost:5434/ragdb2",
    "collection_name": "dell_docs",
}