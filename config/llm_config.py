# AG2 Compatible LLM Configuration
# Removed unsupported parameters: frequency_penalty, presence_penalty

llm_config = {
    "config_list": [
        {
            "model": "mistral-nemo:12b",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "price": [0.0, 0.0],
        }
    ],
    "timeout": 300,
    "temperature": 0.1,
    "max_tokens": 1024,
    "top_p": 0.9,
    # Note: frequency_penalty and presence_penalty are not supported in AG2
}