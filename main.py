# from autogen import AssistantAgent
# from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
# from utils.rag_utils import pdf_to_txt, resolve_docs
# import logging

# logger = logging.getLogger(__name__)

# AGENT_PDF_MAP = {
#     "ChannelAgent": ["VL.pdf"],
#     "EntitlementAnalyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
#     "DamageAnalyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
#     "DecisionOrchestrator": [],
#     "RetrievalAgent": ["VL.pdf", "AccidentalDamage.pdf", "DELLSW.pdf", "BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]  # Default mapping
# }

# class CustomRetrievalAgent(RetrieveUserProxyAgent):
#     def __init__(self, name, llm_config):
#         docs = []
#         if name in AGENT_PDF_MAP:
#             docs = resolve_docs(AGENT_PDF_MAP[name])
#             logger.info(f"Mapped {len(docs)} PDFs for agent {name}: {docs}")
#         else:
#             logger.warning(f"No PDFs mapped for agent {name}, using all available PDFs")
#             docs = resolve_docs([
#                 "VL.pdf", "AccidentalDamage.pdf", "DELLSW.pdf",
#                 "BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"
#             ])

#         super().__init__(
#             name=f"{name}_RetrievalAgent",
#             retrieve_config={
#                 "docs_path": docs,
#                 "collection_name": f"dell_support_{name.lower()}",
#                 "vector_db": "pgvector",
#                 "db_config": {"connection_string": "postgresql://your_user:your_password@localhost:5432/dell_support"},
#                 "chunk_token_size": 512,
#                 "model": "text-embedding-ada-002",
#                 "get_or_create": True,
#                 "k": 5
#             },
#             code_execution_config=False,
#             llm_config=llm_config,
#             system_message="""You are a custom RetrievalAgent in Dell's technical support workflow. Your role is to fetch exactly 5 relevant chunks from the vector DB for a given agent's query, based on the PDFs mapped to that agent.

# **Role Description**:
# - You fetch chunks from specific PDFs assigned to the calling agent.
# - You validate the context of retrieved chunks to ensure relevance.
# - You return raw chunks to the calling agent for summarization.

# **Processing Instructions**:
# 1. Validate Caller:
#    - Ensure the query comes from a valid agent (ChannelAgent, EntitlementAnalyzer, DamageAnalyzer).
#    - Log: "Received query from <agent_name>"
# 2. Fetch Chunks:
#    - Use the provided query to fetch exactly 5 chunks from the vector DB.
#    - Log: "Retrieved {len(chunks)} chunks for <agent_name> from <pdfs>"
# 3. Validate Context:
#    - Check if chunks are relevant to the query.
#    - Log: "Returning {len(valid_chunks)} chunks to <agent_name>"
# """
#         )

#     async def retrieve_chunks(self, query, agent_name):
#         """Fetch exactly 5 chunks for the given agent and query."""
#         try:
#             if agent_name not in AGENT_PDF_MAP:
#                 logger.error(f"Invalid agent {agent_name}")
#                 return []

#             logger.info(f"Received query from {agent_name}: {query}")
#             chunks = await self.retrieve_docs(query=query)
#             logger.info(f"Retrieved {len(chunks)} chunks for {agent_name} from {AGENT_PDF_MAP[agent_name]}")

#             valid_chunks = [chunk for chunk in chunks if self._is_relevant(chunk, query, agent_name)]
#             logger.info(f"Returning {len(valid_chunks)} valid chunks to {agent_name}")
#             return valid_chunks[:5]
#         except Exception as e:
#             logger.error(f"Error retrieving chunks for {agent_name}: {e}")
#             return []

#     def _is_relevant(self, chunk, query, agent_name):
#         """Validate chunk relevance based on agent and query."""
#         keywords = {
#             "ChannelAgent": ["upload", "image", "instructions"],
#             "EntitlementAnalyzer": ["entitlement", "warranty", "accidental damage"],
#             "DamageAnalyzer": ["damage", "biohazard", "monitor", "customer-induced"],
#             "RetrievalAgent": ["upload", "entitlement", "damage", "warranty", "biohazard"]
#         }
#         agent_keywords = keywords.get(agent_name, [])
#         return any(keyword.lower() in chunk.lower() for keyword in agent_keywords) or \
#                any(keyword.lower() in query.lower() for keyword in agent_keywords)

# def create_retrieval_agent(llm_config, agent_name):
#     return CustomRetrievalAgent(name=agent_name, llm_config=llm_config)

























# import autogen
# from autogen import GroupChat, GroupChatManager
# from config.llm_config import llm_config
# from agents.decision_orchestrator import create_decision_orchestrator
# from agents.channel_agent import create_channel_agent
# from agents.damage_analyzer import create_damage_analyzer
# from agents.entitlement_analyzer import create_entitlement_analyzer
# from agents.user_proxy import create_user_proxy
# from agents.retrieval_agent import create_retrieval_agent
# import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# def select_agents(scenario_message):
#     vl_model_output = ""
#     for line in scenario_message.split('\n'):
#         if "VL Model Output:" in line:
#             vl_model_output = line.split(":")[1].strip().lower()

#     if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
#         return ["UserProxyAgent", "ChannelAgent", "RetrievalAgent", "DecisionOrchestrator"]
#     return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "RetrievalAgent", "DecisionOrchestrator"]

# def main():
#     try:
#         user_proxy = create_user_proxy(llm_config)
#         decision_orchestrator = create_decision_orchestrator(llm_config)
#         channel_agent = create_channel_agent(llm_config)
#         damage_analyzer = create_damage_analyzer(llm_config)
#         entitlement_analyzer = create_entitlement_analyzer(llm_config)
#         retrieval_agent = create_retrieval_agent(llm_config, "RetrievalAgent")

#         all_agents = {
#             "UserProxyAgent": user_proxy,
#             "DecisionOrchestrator": decision_orchestrator,
#             "ChannelAgent": channel_agent,
#             "DamageAnalyzer": damage_analyzer,
#             "EntitlementAnalyzer": entitlement_analyzer,
#             "RetrievalAgent": retrieval_agent
#         }

#         scenario = """Scenario details:
# 1. Service Tag: AXBYCZ6
# 2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
# 3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
# 4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days - so AD WO cannot be created
# 5. VL Model Output: VL Model did not find any image or format is invalid
# 6. Region: Australia
# 7. Damage Description: dropped the system"""

#         selected_agent_names = select_agents(scenario)
#         selected_agents = [all_agents[name] for name in selected_agent_names]

#         logging.info(f"Selected agent names: {selected_agent_names}")

#         group_chat = GroupChat(
#             agents=selected_agents,
#             max_round=5,
#             speaker_selection_method="auto",
#             allow_repeat_speaker=False,
#         )

#         def is_termination_msg(message):
#             logging.info(f"Checking termination message: {message}")
#             return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]

#         manager = GroupChatManager(
#             groupchat=group_chat,
#             llm_config=llm_config,
#             system_message="""You are the GroupChatManager, coordinating a multi-agent technical support workflow at Dell. Your role is to manage conversation flow, ensuring each agent contributes exactly once per cycle.

# **Agents**:
# - @UserProxyAgent: Validates and forwards scenario.
# - @ChannelAgent: Provides image upload instructions (Scenario 1).
# - @EntitlementAnalyzer: Verifies eligibility (Scenario 2).
# - @DamageAnalyzer: Assesses damage (Scenario 2).
# - @RetrievalAgent: Supports RAG queries.
# - @DecisionOrchestrator: Makes final decision.

# **Speaker Selection**:
# 1. Start with @UserProxyAgent.
# 2. For VL_STATUS = NO_IMAGE_FOUND:
#    - @ChannelAgent: "Please provide image upload instructions: Service Tag: <...> Region: <...> VL Model Output: No image data available"
#    - @RetrievalAgent: Support ChannelAgent if needed.
#    - @DecisionOrchestrator: Finalize decision.
# 3. For VL_STATUS = IMAGE_PROCESSED:
#    - @EntitlementAnalyzer: "Please verify entitlement: Service Tag: <...> AD Entitlement: <...> AD Incident Available: <...> AD Cooling Period: <...> Region: <...> Damage Description: <...>"
#    - @DamageAnalyzer: "Please analyze damage: Service Tag: <...> Damage Description: <...> VL Model Output: <...>"
#    - @RetrievalAgent: Support analyzers if needed.
#    - @DecisionOrchestrator: Finalize decision.

# **Output Format**:
# Next speaker: @AgentName
# Reason: [Why this agent was selected]
# """,
#             is_termination_msg=is_termination_msg
#         )

#         chat_result = user_proxy.initiate_chat(
#             manager,
#             message=scenario,
#             silent=False
#         )

#         final_message = None
#         for msg in reversed(chat_result.chat_history):
#             if msg.get('name') == 'DecisionOrchestrator':
#                 final_message = msg['content']
#                 break

#         if final_message:
#             print("\n=== FINAL DECISION ===")
#             print(final_message)
#             print("======================")
#         else:
#             print("No final decision was generated by the DecisionOrchestrator.")

#     except Exception as e:
#         logger.error(f"Error in main: {e}")
#         raise

# if __name__ == "__main__":
#     main()















































# import autogen
# from autogen import GroupChat, GroupChatManager
# from config.llm_config import llm_config
# from agents.decision_orchestrator import create_decision_orchestrator
# from agents.channel_agent import create_channel_agent
# from agents.damage_analyzer import create_damage_analyzer
# from agents.entitlement_analyzer import create_entitlement_analyzer
# from agents.user_proxy import create_user_proxy
# from agents.retrieval_agent import create_retrieval_agent
# import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# def select_agents(scenario_message):
#     vl_model_output = ""
#     for line in scenario_message.split('\n'):
#         if "VL Model Output:" in line:
#             vl_model_output = line.split(":")[1].strip().lower()

#     if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
#         return ["UserProxyAgent", "ChannelAgent", "RetrievalAgent", "DecisionOrchestrator"]
#     return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "RetrievalAgent", "DecisionOrchestrator"]

# def main():
#     try:
#         user_proxy = create_user_proxy(llm_config)
#         decision_orchestrator = create_decision_orchestrator(llm_config)
#         channel_agent = create_channel_agent(llm_config)
#         damage_analyzer = create_damage_analyzer(llm_config)
#         entitlement_analyzer = create_entitlement_analyzer(llm_config)
#         retrieval_agent = create_retrieval_agent(llm_config, "RetrievalAgent")

#         all_agents = {
#             "UserProxyAgent": user_proxy,
#             "DecisionOrchestrator": decision_orchestrator,
#             "ChannelAgent": channel_agent,
#             "DamageAnalyzer": damage_analyzer,
#             "EntitlementAnalyzer": entitlement_analyzer,
#             "RetrievalAgent": retrieval_agent
#         }

#         scenario = """Scenario details:
# 1. Service Tag: AXBYCZ6
# 2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
# 3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
# 4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days
# 5. VL Model Output: VL Model did not find any image or format is invalid
# 6. Region: Australia
# 7. Damage Description: dropped the system"""

#         selected_agent_names = select_agents(scenario)
#         selected_agents = [all_agents[name] for name in selected_agent_names]

#         logger.info(f"Selected agent names: {selected_agent_names}")

#         group_chat = GroupChat(
#             agents=selected_agents,
#             max_round=5,
#             speaker_selection_method="auto",
#             allow_repeat_speaker=False,
#         )

#         def is_termination_msg(message):
#             logger.info(f"Checking termination message: {message}")
#             return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]

#         manager = GroupChatManager(
#             groupchat=group_chat,
#             llm_config=llm_config,
#             system_message="""You are the GroupChatManager, coordinating a multi-agent technical support workflow at Dell. Your role is to manage conversation flow, ensuring each agent contributes exactly once per cycle.

# **Agents**:
# - @UserProxyAgent: Validates and forwards scenario.
# - @ChannelAgent: Provides image upload instructions (Scenario 1).
# - @EntitlementAnalyzer: Verifies eligibility (Scenario 2).
# - @DamageAnalyzer: Assesses damage (Scenario 2).
# - @RetrievalAgent: Supports RAG queries.
# - @DecisionOrchestrator: Makes final decision.

# **Speaker Selection**:
# 1. Start with @UserProxyAgent.
# 2. For VL_STATUS = NO_IMAGE_FOUND:
#    - @ChannelAgent: "Please provide image upload instructions: Service Tag: <...> Region: <...> VL Model Output: No image data available"
#    - @RetrievalAgent: Support ChannelAgent if needed.
#    - @DecisionOrchestrator: Finalize decision.
# 3. For VL_STATUS = IMAGE_PROCESSED:
#    - @EntitlementAnalyzer: "Please verify entitlement: Service Tag: <...> AD Entitlement: <...> AD Incident Available: <...> AD Cooling Period: <...> Region: <...> Damage Description: <...>"
#    - @DamageAnalyzer: "Please analyze damage: Service Tag: <...> Damage Description: <...> VL Model Output: <...>"
#    - @RetrievalAgent: Support analyzers if needed.
#    - @DecisionOrchestrator: Finalize decision.

# **Output Format**:
# Next speaker: @AgentName
# Reason: [Why this agent was selected]
# """,
#             is_termination_msg=is_termination_msg
#         )

#         chat_result = user_proxy.initiate_chat(
#             manager,
#             message=scenario,
#             silent=False
#         )

#         final_message = None
#         for msg in reversed(chat_result.chat_history):
#             if msg.get('name') == 'DecisionOrchestrator':
#                 final_message = msg['content']
#                 break

#         if final_message:
#             print("\n=== FINAL DECISION ===")
#             print(final_message)
#             print("======================")
#         else:
#             print("No final decision was generated by the DecisionOrchestrator.")

#     except Exception as e:
#         logger.error(f"Error in main: {e}")
#         raise

# if __name__ == "__main__":
#     main()




































# import autogen
# from autogen import GroupChat, GroupChatManager
# from config.llm_config import llm_config
# from agents.decision_orchestrator import create_decision_orchestrator
# from agents.channel_agent import create_channel_agent
# from agents.damage_analyzer import create_damage_analyzer
# from agents.entitlement_analyzer import create_entitlement_analyzer
# from agents.user_proxy import create_user_proxy
# from agents.retrieval_agent import create_retrieval_agent
# import logging
# import time
# import random
# import requests
# import subprocess
# import psycopg2

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Your working configuration
# LLM_BASE_URL = "http://localhost:11434/v1"
# DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"
# EMBED_MODEL = "nomic-embed-text:latest"
# CHUNK_TOKENS = 200
# TOP_K = 1

# CONFIG_LIST = [{
#     "model": "llama3.1:8b",
#     "base_url": LLM_BASE_URL,
#     "api_key": "ollama",
#     "price": [0.0, 0.0],
# }]

# DOC_MAP = {
#     "damage_analyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
#     "entitlement_analyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
#     "vl_agent": ["VL.pdf"],
# }

# def check_ollama_status():
#     """Check if Ollama server is running with your specific model"""
#     try:
#         response = requests.get("http://localhost:11434/api/tags", timeout=10)
#         if response.status_code == 200:
#             models = response.json()
#             available_models = [model['name'] for model in models.get('models', [])]
#             logger.info(f"Ollama server accessible. Available models: {available_models}")
            
#             return True
#         else:
#             logger.error(f"Ollama server responded with status: {response.status_code}")
#             return False
#     except requests.exceptions.ConnectionError:
#         logger.error("✗ Cannot connect to Ollama server at localhost:11434")
#         return False
#     except Exception as e:
#         logger.error(f"Error checking Ollama: {e}")
#         return False

# def check_postgres_connection():
#     """Check PostgreSQL connection"""
#     try:
#         conn = psycopg2.connect(DB_CONN)
#         conn.close()
#         logger.info("✓ PostgreSQL connection successful")
#         return True
#     except Exception as e:
#         logger.error(f"✗ PostgreSQL connection failed: {e}")
#         return False

# def check_embedding_model():
#     """Check if embedding model is available"""
#     try:
#         response = requests.get("http://localhost:11434/api/tags", timeout=5)
#         if response.status_code == 200:
#             models = response.json()
#             available_models = [model['name'] for model in models.get('models', [])]
            
#             if EMBED_MODEL in available_models:
#                 logger.info(f"✓ Embedding model {EMBED_MODEL} is available")
#                 return True
#             else:
#                 logger.warning(f"✗ Embedding model {EMBED_MODEL} not found")
#                 logger.info("Run: ollama pull nomic-embed-text")
#                 return False
#     except Exception as e:
#         logger.error(f"Error checking embedding model: {e}")
#         return False

# def test_llama_inference():
#     """Test inference with your specific model"""
#     try:
#         payload = {
#             "model": "llama3.1:8b",
#             "prompt": "Hello, respond with just 'OK'",
#             "stream": False,
#             "options": {
#                 "temperature": 0.1,
#                 "num_predict": 5
#             }
#         }
        
#         response = requests.post("http://localhost:11434/api/generate", 
#                                json=payload, timeout=30)
        
#         if response.status_code == 200:
#             result = response.json()
#             logger.info(f"✓ Model inference test successful: {result.get('response', 'No response')[:50]}")
#             return True
#         else:
#             logger.error(f"✗ Model inference failed: {response.status_code}")
#             return False
#     except Exception as e:
#         logger.error(f"Model inference test error: {e}")
#         return False

# def create_working_llm_config():
#     """Create LLM config using your working setup"""
#     return {
#         "config_list": CONFIG_LIST,
#         "timeout": 120,
#         "temperature": 0.1,
#         "max_tokens": 1024,  # Reduced for efficiency
#         # "request_timeout": 60,
#     }

# def exponential_backoff_retry(func, max_retries=3, base_delay=2):
#     """Simple retry logic for connection issues"""
#     for attempt in range(max_retries):
#         try:
#             return func()
#         except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
#             if attempt == max_retries - 1:
#                 logger.error(f"Max retries ({max_retries}) exceeded. Last error: {e}")
#                 raise
            
#             delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
#             logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
#             time.sleep(delay)
#         except Exception as e:
#             logger.error(f"Non-retryable error: {e}")
#             raise

# def select_agents(scenario_message):
#     vl_model_output = ""
#     for line in scenario_message.split('\n'):
#         if "VL Model Output:" in line:
#             vl_model_output = line.split(":")[1].strip().lower()

#     if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
#         return ["UserProxyAgent", "ChannelAgent", "RetrievalAgent", "DecisionOrchestrator"]
#     return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "RetrievalAgent", "DecisionOrchestrator"]

# def create_agents_safely():
#     """Create agents with retry logic"""
#     working_config = create_working_llm_config()
    
#     def _create_agents():
#         return {
#             "UserProxyAgent": create_user_proxy(working_config),
#             "DecisionOrchestrator": create_decision_orchestrator(working_config),
#             "ChannelAgent": create_channel_agent(working_config),
#             "DamageAnalyzer": create_damage_analyzer(working_config),
#             "EntitlementAnalyzer": create_entitlement_analyzer(working_config),
#             "RetrievalAgent": create_retrieval_agent(working_config, "RetrievalAgent")
#         }
    
#     return exponential_backoff_retry(_create_agents)

# def run_chat_safely(user_proxy, manager, scenario):
#     """Run chat with retry logic"""
#     def _run_chat():
#         return user_proxy.initiate_chat(
#             manager,
#             message=scenario,
#             silent=False
#         )
    
#     return exponential_backoff_retry(_run_chat, max_retries=2)

# def main():
#     try:
#         logger.info("🚀 Starting Dell Technical Support Multi-Agent System")
#         logger.info(f"Using model: llama3.1:8b")
#         logger.info(f"Ollama endpoint: {LLM_BASE_URL}")
#         logger.info(f"Database: {DB_CONN.split('@')[1] if '@' in DB_CONN else DB_CONN}")
        
#         # System checks
#         logger.info("🔍 Running system checks...")
        
#         if not check_ollama_status():
#             logger.error("❌ Ollama check failed. Please ensure:")
#             logger.error("  1. ollama serve is running")
#             logger.error("  2. Model is available: ollama pull llama3.1:8b")
#             return
        
#         if not check_postgres_connection():
#             logger.error("❌ PostgreSQL check failed. Please ensure:")
#             logger.error("  1. PostgreSQL is running on port 5432")
#             logger.error("  2. Database 'ragdb2' exists with correct credentials")
#             return
        
#         if not check_embedding_model():
#             logger.warning("⚠️  Embedding model check failed, but continuing...")
        
#         if not test_llama_inference():
#             logger.error("❌ Model inference test failed")
#             return
            
#         logger.info("✅ All system checks passed!")
        
#         # Create agents
#         logger.info("🤖 Creating agents...")
#         all_agents = create_agents_safely()
#         logger.info("✅ All agents created successfully")
        
#         # Scenario
#         scenario = """Scenario details:
# 1. Service Tag: AXBYCZ6
# 2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
# 3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
# 4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days
# 5. VL Model Output: VL Model did not find any image or format is invalid
# 6. Region: Australia
# 7. Damage Description: dropped the system"""

#         selected_agent_names = select_agents(scenario)
#         selected_agents = [all_agents[name] for name in selected_agent_names]
#         logger.info(f"📋 Selected agents: {selected_agent_names}")

#         # Group chat setup
#         group_chat = GroupChat(
#             agents=selected_agents,
#             max_round=4,  # Keep it manageable
#             speaker_selection_method="auto",
#             allow_repeat_speaker=False,
#         )

#         def is_termination_msg(message):
#             logger.debug(f"Checking termination: {message}")
#             return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]

#         working_config = create_working_llm_config()
#         manager = GroupChatManager(
#             groupchat=group_chat,
#             llm_config=working_config,
#             system_message="""You are the GroupChatManager for Dell Technical Support using local Llama model.

# **Workflow**:
# 1. @UserProxyAgent: Validate scenario
# 2. Since VL shows "no image found":
#    - @ChannelAgent: Provide image upload instructions
#    - @RetrievalAgent: Support with documentation if needed  
#    - @DecisionOrchestrator: Make final decision

# **Rules**:
# - Keep responses concise for local model efficiency
# - Always end final decision with "TERMINATE"
# - Focus on the specific scenario provided
# """,
#             is_termination_msg=is_termination_msg
#         )

#         # Run the conversation
#         logger.info("💬 Starting group chat...")
#         chat_result = run_chat_safely(all_agents["UserProxyAgent"], manager, scenario)

#         # Extract final decision
#         final_message = None
#         for msg in reversed(chat_result.chat_history):
#             if msg.get('name') == 'DecisionOrchestrator':
#                 final_message = msg['content']
#                 break

#         if final_message:
#             print("\n" + "="*50)
#             print("🎯 FINAL DECISION")
#             print("="*50)
#             print(final_message)
#             print("="*50)
#         else:
#             print("❌ No final decision was generated by the DecisionOrchestrator.")
            
#         logger.info("✅ Multi-agent system completed successfully")

#     except KeyboardInterrupt:
#         logger.info("⏹️  Process interrupted by user")
#     except requests.exceptions.ConnectionError as e:
#         logger.error(f"🔌 Connection error: {e}")
#         logger.error("Check: ollama serve & PostgreSQL running")
#     except Exception as e:
#         logger.error(f"💥 Unexpected error: {e}")
#         logger.exception("Full traceback:")

# if __name__ == "__main__":
#     main()


































# import autogen
# from autogen import GroupChat, GroupChatManager
# from config.llm_config import llm_config
# from agents.decision_orchestrator import create_decision_orchestrator
# from agents.channel_agent import create_channel_agent
# from agents.damage_analyzer import create_damage_analyzer
# from agents.entitlement_analyzer import create_entitlement_analyzer
# from agents.user_proxy import create_user_proxy
# from agents.retrieval_agent import create_retrieval_agent
# import logging
# import time
# import random
# import requests
# import subprocess
# import psycopg2

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Your working configuration
# LLM_BASE_URL = "http://localhost:11434/v1"
# DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"
# EMBED_MODEL = "nomic-embed-text:latest"
# CHUNK_TOKENS = 200
# TOP_K = 1

# CONFIG_LIST = [{
#     "model": "llama3.1:8b",
#     "base_url": LLM_BASE_URL,
#     "api_key": "ollama",
#     "price": [0.0, 0.0],
# }]

# DOC_MAP = {
#     "damage_analyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
#     "entitlement_analyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
#     "vl_agent": ["VL.pdf"],
# }

# def check_ollama_status():
#     """Check if Ollama server is running with your specific model"""
#     try:
#         response = requests.get("http://localhost:11434/api/tags", timeout=10)
#         if response.status_code == 200:
#             models = response.json()
#             available_models = [model['name'] for model in models.get('models', [])]
#             logger.info(f"Ollama server accessible. Available models: {available_models}")
#             return True
#         else:
#             logger.error(f"Ollama server responded with status: {response.status_code}")
#             return False
#     except requests.exceptions.ConnectionError:
#         logger.error("✗ Cannot connect to Ollama server at localhost:11434")
#         return False
#     except Exception as e:
#         logger.error(f"Error checking Ollama: {e}")
#         return False

# def check_postgres_connection():
#     """Check PostgreSQL connection"""
#     try:
#         conn = psycopg2.connect(DB_CONN)
#         conn.close()
#         logger.info("✓ PostgreSQL connection successful")
#         return True
#     except Exception as e:
#         logger.error(f"✗ PostgreSQL connection failed: {e}")
#         return False

# def check_embedding_model():
#     """Check if embedding model is available"""
#     try:
#         response = requests.get("http://localhost:11434/api/tags", timeout=5)
#         if response.status_code == 200:
#             models = response.json()
#             available_models = [model['name'] for model in models.get('models', [])]
#             if EMBED_MODEL in available_models:
#                 logger.info(f"✓ Embedding model {EMBED_MODEL} is available")
#                 return True
#             else:
#                 logger.warning(f"✗ Embedding model {EMBED_MODEL} not found")
#                 logger.info("Run: ollama pull nomic-embed-text")
#                 return False
#     except Exception as e:
#         logger.error(f"Error checking embedding model: {e}")
#         return False

# def test_llama_inference():
#     """Test inference with your specific model"""
#     try:
#         payload = {
#             "model": "llama3.1:8b",
#             "prompt": "Hello, respond with just 'OK'",
#             "stream": False,
#             "options": {
#                 "temperature": 0.1,
#                 "num_predict": 5
#             }
#         }
#         response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
#         if response.status_code == 200:
#             result = response.json()
#             logger.info(f"✓ Model inference test successful: {result.get('response', 'No response')[:50]}")
#             return True
#         else:
#             logger.error(f"✗ Model inference failed: {response.status_code}")
#             return False
#     except Exception as e:
#         logger.error(f"Model inference test error: {e}")
#         return False

# def create_working_llm_config():
#     """Create LLM config using your working setup"""
#     return {
#         "config_list": CONFIG_LIST,
#         "timeout": 120,
#         "temperature": 0.1,
#         "max_tokens": 1024,
#     }

# def exponential_backoff_retry(func, max_retries=3, base_delay=2):
#     """Simple retry logic for connection issues"""
#     for attempt in range(max_retries):
#         try:
#             return func()
#         except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
#             if attempt == max_retries - 1:
#                 logger.error(f"Max retries ({max_retries}) exceeded. Last error: {e}")
#                 raise
#             delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
#             logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
#             time.sleep(delay)
#         except Exception as e:
#             logger.error(f"Non-retryable error: {e}")
#             raise

# def select_agents(scenario_message):
#     vl_model_output = ""
#     for line in scenario_message.split('\n'):
#         if "VL Model Output:" in line:
#             vl_model_output = line.split(":")[1].strip().lower()
#     if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
#         return ["UserProxyAgent", "ChannelAgent", "RetrievalAgent", "DecisionOrchestrator"]
#     return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "RetrievalAgent", "DecisionOrchestrator"]

# def create_agents_safely():
#     """Create agents with retry logic"""
#     working_config = create_working_llm_config()
#     def _create_agents():
#         return {
#             "UserProxyAgent": create_user_proxy(working_config),
#             "DecisionOrchestrator": create_decision_orchestrator(working_config),
#             "ChannelAgent": create_channel_agent(working_config),
#             "DamageAnalyzer": create_damage_analyzer(working_config),
#             "EntitlementAnalyzer": create_entitlement_analyzer(working_config),
#             "RetrievalAgent": create_retrieval_agent(working_config, "RetrievalAgent")
#         }
#     return exponential_backoff_retry(_create_agents)

# def run_chat_safely(user_proxy, manager, scenario):
#     """Run chat with retry logic"""
#     def _run_chat():
#         return user_proxy.initiate_chat(
#             manager,
#             message=scenario,
#             silent=False
#         )
#     return exponential_backoff_retry(_run_chat, max_retries=2)

# def custom_speaker_selection(last_speaker, groupchat):
#     """Custom speaker selection to enforce order"""
#     agents = groupchat.agents
#     agent_names = [agent.name for agent in agents]
#     logger.debug(f"Last speaker: {last_speaker.name if last_speaker else 'None'}, Available agents: {agent_names}")

#     if not last_speaker:
#         logger.debug("Selecting UserProxyAgent as first speaker")
#         return agents[agent_names.index("UserProxyAgent")]
#     elif last_speaker.name == "UserProxyAgent":
#         logger.debug("Selecting ChannelAgent after UserProxyAgent")
#         return agents[agent_names.index("ChannelAgent")]
#     elif last_speaker.name == "ChannelAgent":
#         logger.debug("Selecting RetrievalAgent after ChannelAgent")
#         return agents[agent_names.index("RetrievalAgent")]
#     elif last_speaker.name == "RetrievalAgent":
#         logger.debug("Selecting DecisionOrchestrator after RetrievalAgent")
#         return agents[agent_names.index("DecisionOrchestrator")]
#     else:
#         logger.warning(f"Unexpected last speaker: {last_speaker.name}")
#         return None

# def main():
#     try:
#         logger.info("🚀 Starting Dell Technical Support Multi-Agent System")
#         logger.info(f"Using model: llama3.1:8b")
#         logger.info(f"Ollama endpoint: {LLM_BASE_URL}")
#         logger.info(f"Database: {DB_CONN.split('@')[1] if '@' in DB_CONN else DB_CONN}")
#         # System checks
#         logger.info("🔍 Running system checks...")
#         if not check_ollama_status():
#             logger.error("❌ Ollama check failed. Please ensure:")
#             logger.error("  1. ollama serve is running")
#             logger.error("  2. Model is available: ollama pull llama3.1:8b")
#             return
#         if not check_postgres_connection():
#             logger.error("❌ PostgreSQL check failed. Please ensure:")
#             logger.error("  1. PostgreSQL is running on port 5432")
#             logger.error("  2. Database 'ragdb2' exists with correct credentials")
#             return
#         if not check_embedding_model():
#             logger.warning("⚠️  Embedding model check failed, but continuing...")
#         if not test_llama_inference():
#             logger.error("❌ Model inference test failed")
#             return
#         logger.info("✅ All system checks passed!")
#         # Create agents
#         logger.info("🤖 Creating agents...")
#         all_agents = create_agents_safely()
#         logger.info("✅ All agents created successfully")
#         # Scenario
#         scenario = """Scenario details:
# 1. Service Tag: AXBYCZ6
# 2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
# 3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
# 4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days
# 5. VL Model Output: VL Model did not find any image or format is invalid
# 6. Region: Australia
# 7. Damage Description: dropped the system"""
#         selected_agent_names = select_agents(scenario)
#         selected_agents = [all_agents[name] for name in selected_agent_names]
#         logger.info(f"📋 Selected agents: {selected_agent_names}")
#         # Group chat setup
#         group_chat = GroupChat(
#             agents=selected_agents,
#             max_round=4,
#             speaker_selection_method=custom_speaker_selection,
#             allow_repeat_speaker=False,
#         )
#         def is_termination_msg(message):
#             logger.debug(f"Checking termination: {message}")
#             return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]
#         working_config = create_working_llm_config()
#         manager = GroupChatManager(
#             groupchat=group_chat,
#             llm_config=working_config,
#             system_message="""You are the GroupChatManager for Dell Technical Support using local Llama model.

# **Workflow**:
# 1. @UserProxyAgent: Validate scenario
# 2. Since VL shows "no image found":
#    - @ChannelAgent: Provide image upload instructions
#    - @RetrievalAgent: Support with documentation if needed  
#    - @DecisionOrchestrator: Make final decision

# **Rules**:
# - Keep responses concise for local model efficiency
# - Always end final decision with "TERMINATE"
# - Focus on the specific scenario provided
# - Follow speaker order: UserProxyAgent -> ChannelAgent -> RetrievalAgent -> DecisionOrchestrator
# """,
#             is_termination_msg=is_termination_msg
#         )
#         # Run the conversation
#         logger.info("💬 Starting group chat...")
#         chat_result = run_chat_safely(all_agents["UserProxyAgent"], manager, scenario)
#         # Extract final decision
#         final_message = None
#         for msg in reversed(chat_result.chat_history):
#             if msg.get('name') == 'DecisionOrchestrator':
#                 final_message = msg['content']
#                 break
#         if final_message:
#             print("\n" + "="*50)
#             print("🎯 FINAL DECISION")
#             print("="*50)
#             print(final_message)
#             print("="*50)
#         else:
#             print("❌ No final decision was generated by the DecisionOrchestrator.")
#         logger.info("✅ Multi-agent system completed successfully")
#     except KeyboardInterrupt:
#         logger.info("⏹️  Process interrupted by user")
#     except requests.exceptions.ConnectionError as e:
#         logger.error(f"🔌 Connection error: {e}")
#         logger.error("Check: ollama serve & PostgreSQL running")
#     except Exception as e:
#         logger.error(f"💥 Unexpected error: {e}")
#         logger.exception("Full traceback:")
# if __name__ == "__main__":
#     main()






























import autogen
from autogen import GroupChat, GroupChatManager
from config.llm_config import llm_config
from agents.decision_orchestrator import create_decision_orchestrator
from agents.channel_agent import create_channel_agent
from agents.damage_analyzer import create_damage_analyzer
from agents.entitlement_analyzer import create_entitlement_analyzer
from agents.user_proxy import create_user_proxy
from agents.retrieval_agent import create_retrieval_agent
import logging
import time
import random
import requests
import subprocess
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your working configuration
LLM_BASE_URL = "http://localhost:11434/v1"
DB_CONN = "postgresql://postgres:myragpw@localhost:5432/ragdb2"
EMBED_MODEL = "nomic-embed-text:latest"
CHUNK_TOKENS = 200
TOP_K = 1

CONFIG_LIST = [{
    "model": "llama3.1:8b",
    "base_url": LLM_BASE_URL,
    "api_key": "ollama",
    "price": [0.0, 0.0],
}]

DOC_MAP = {
    "damage_analyzer": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"],
    "entitlement_analyzer": ["AccidentalDamage.pdf", "DELLSW.pdf"],
    "vl_agent": ["VL.pdf"],
}

def check_ollama_status():
    """Check if Ollama server is running with your specific model"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            available_models = [model['name'] for model in models.get('models', [])]
            logger.info(f"Ollama server accessible. Available models: {available_models}")
            return True
        else:
            logger.error(f"Ollama server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("✗ Cannot connect to Ollama server at localhost:11434")
        return False
    except Exception as e:
        logger.error(f"Error checking Ollama: {e}")
        return False

def check_postgres_connection():
    """Check PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DB_CONN)
        conn.close()
        logger.info("✓ PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection failed: {e}")
        return False

def check_embedding_model():
    """Check if embedding model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            available_models = [model['name'] for model in models.get('models', [])]
            if EMBED_MODEL in available_models:
                logger.info(f"✓ Embedding model {EMBED_MODEL} is available")
                return True
            else:
                logger.warning(f"✗ Embedding model {EMBED_MODEL} not found")
                logger.info("Run: ollama pull nomic-embed-text")
                return False
    except Exception as e:
        logger.error(f"Error checking embedding model: {e}")
        return False

def test_llama_inference():
    """Test inference with your specific model"""
    try:
        payload = {
            "model": "llama3.1:8b",
            "prompt": "Hello, respond with just 'OK'",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 5
            }
        }
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Model inference test successful: {result.get('response', 'No response')[:50]}")
            return True
        else:
            logger.error(f"✗ Model inference failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Model inference test error: {e}")
        return False

def create_working_llm_config():
    """Create LLM config using your working setup"""
    return {
        "config_list": CONFIG_LIST,
        "timeout": 120,
        "temperature": 0.1,
        "max_tokens": 1024,
    }

def exponential_backoff_retry(func, max_retries=3, base_delay=2):
    """Simple retry logic for connection issues"""
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retries - 1:
                logger.error(f"Max retries ({max_retries}) exceeded. Last error: {e}")
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Non-retryable error: {e}")
            raise

def select_agents(scenario_message):
    vl_model_output = ""
    for line in scenario_message.split('\n'):
        if "VL Model Output:" in line:
            vl_model_output = line.split(":")[1].strip().lower()
    if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
        return ["UserProxyAgent", "ChannelAgent", "RetrievalAgent", "DecisionOrchestrator"]
    return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "RetrievalAgent", "DecisionOrchestrator"]

def create_agents_safely():
    """Create agents with retry logic"""
    working_config = create_working_llm_config()
    def _create_agents():
        return {
            "UserProxyAgent": create_user_proxy(working_config),
            "DecisionOrchestrator": create_decision_orchestrator(working_config),
            "ChannelAgent": create_channel_agent(working_config),
            "DamageAnalyzer": create_damage_analyzer(working_config),
            "EntitlementAnalyzer": create_entitlement_analyzer(working_config),
            "RetrievalAgent": create_retrieval_agent(working_config, "RetrievalAgent")
        }
    return exponential_backoff_retry(_create_agents)

def run_chat_safely(user_proxy, manager, scenario):
    """Run chat with retry logic"""
    def _run_chat():
        return user_proxy.initiate_chat(
            manager,
            message=scenario,
            silent=False
        )
    return exponential_backoff_retry(_run_chat, max_retries=2)

def custom_speaker_selection(last_speaker, groupchat):
    """Custom speaker selection to enforce order"""
    agents = groupchat.agents
    agent_names = [agent.name for agent in agents]
    logger.debug(f"Last speaker: {last_speaker.name if last_speaker else 'None'}, Available agents: {agent_names}")

    if not last_speaker:
        logger.debug("Selecting UserProxyAgent as first speaker")
        return agents[agent_names.index("UserProxyAgent")]
    elif last_speaker.name == "UserProxyAgent":
        logger.debug("Selecting ChannelAgent after UserProxyAgent")
        return agents[agent_names.index("ChannelAgent")]
    elif last_speaker.name == "ChannelAgent":
        logger.debug("Selecting RetrievalAgent after ChannelAgent")
        return agents[agent_names.index("RetrievalAgent")]
    elif last_speaker.name == "RetrievalAgent":
        logger.debug("Selecting DecisionOrchestrator after RetrievalAgent")
        return agents[agent_names.index("DecisionOrchestrator")]
    else:
        logger.warning(f"Unexpected last speaker: {last_speaker.name}")
        return None

def main():
    try:
        logger.info("🚀 Starting Dell Technical Support Multi-Agent System")
        logger.info(f"Using model: llama3.1:8b")
        logger.info(f"Ollama endpoint: {LLM_BASE_URL}")
        logger.info(f"Database: {DB_CONN.split('@')[1] if '@' in DB_CONN else DB_CONN}")
        logger.debug("Main function line count check: ~700 lines expected")
        # System checks
        logger.info("🔍 Running system checks...")
        if not check_ollama_status():
            logger.error("❌ Ollama check failed. Please ensure:")
            logger.error("  1. ollama serve is running")
            logger.error("  2. Model is available: ollama pull llama3.1:8b")
            return
        if not check_postgres_connection():
            logger.error("❌ PostgreSQL check failed. Please ensure:")
            logger.error("  1. PostgreSQL is running on port 5432")
            logger.error("  2. Database 'ragdb2' exists with correct credentials")
            return
        if not check_embedding_model():
            logger.warning("⚠️  Embedding model check failed, but continuing...")
        if not test_llama_inference():
            logger.error("❌ Model inference test failed")
            return
        logger.info("✅ All system checks passed!")
        # Create agents
        logger.info("🤖 Creating agents...")
        all_agents = create_agents_safely()
        logger.info("✅ All agents created successfully")
        # Scenario
        scenario = """Scenario details:
1. Service Tag: AXBYCZ6
2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days
5. VL Model Output: VL Model did not find any image or format is invalid
6. Region: Australia
7. Damage Description: dropped the system"""
        selected_agent_names = select_agents(scenario)
        selected_agents = [all_agents[name] for name in selected_agent_names]
        logger.info(f"📋 Selected agents: {selected_agent_names}")
        # Group chat setup
        group_chat = GroupChat(
            agents=selected_agents,
            max_round=4,
            speaker_selection_method=custom_speaker_selection,
            allow_repeat_speaker=False,
        )
        def is_termination_msg(message):
            logger.debug(f"Checking termination: {message}")
            return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]
        working_config = create_working_llm_config()
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=working_config,
            system_message="""You are the GroupChatManager for Dell Technical Support using local Llama model.

**Workflow**:
1. @UserProxyAgent: Validate scenario
2. Since VL shows "no image found":
   - @ChannelAgent: Provide image upload instructions
   - @RetrievalAgent: Support with documentation if needed  
   - @DecisionOrchestrator: Make final decision

**Rules**:
- Keep responses concise for local model efficiency
- Always end final decision with "TERMINATE"
- Focus on the specific scenario provided
- Follow speaker order: UserProxyAgent -> ChannelAgent -> RetrievalAgent -> DecisionOrchestrator
""",
            is_termination_msg=is_termination_msg
        )
        # Run the conversation
        logger.info("💬 Starting group chat...")
        chat_result = run_chat_safely(all_agents["UserProxyAgent"], manager, scenario)
        # Extract final decision
        final_message = None
        for msg in reversed(chat_result.chat_history):
            if msg.get('name') == 'DecisionOrchestrator':
                final_message = msg['content']
                break
        if final_message:
            print("\n" + "="*50)
            print("🎯 FINAL DECISION")
            print("="*50)
            print(final_message)
            print("="*50)
        else:
            print("❌ No final decision was generated by the DecisionOrchestrator.")
        logger.info("✅ Multi-agent system completed successfully")
    except KeyboardInterrupt:
        logger.info("⏹️  Process interrupted by user")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 Connection error: {e}")
        logger.error("Check: ollama serve & PostgreSQL running")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        logger.exception("Full traceback:")
if __name__ == "__main__":
    main()