# import autogen
# from autogen import GroupChat, GroupChatManager
# from config.llm_config import llm_config
# from agents.decision_orchestrator import create_decision_orchestrator
# from agents.channel_agent import create_channel_agent
# from agents.damage_analyzer import create_damage_analyzer
# from agents.entitlement_analyzer import create_entitlement_analyzer
# from agents.user_proxy import create_user_proxy
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# def select_agents(scenario_message):
#     """
#     Selects agents based on the VL Model Output in the scenario.
#     Returns a list of agent names for the appropriate scenario.
#     """
#     vl_model_output = ""
#     for line in scenario_message.split('\n'):
#         if "VL Model Output:" in line:
#             vl_model_output = line.split(":")[1].strip().lower()

#     # Scenario 1: No image detected
#     if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
#         return ["UserProxyAgent", "ChannelAgent", "DecisionOrchestrator"]
#     # Scenario 2: Image processed
#     else:
#         return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "DecisionOrchestrator"]

# def main():
#     # Create agents
#     user_proxy = create_user_proxy(llm_config)
#     decision_orchestrator = create_decision_orchestrator(llm_config)
#     channel_agent = create_channel_agent(llm_config)
#     damage_analyzer = create_damage_analyzer(llm_config)
#     entitlement_analyzer = create_entitlement_analyzer(llm_config)

#     # Map agent names to agent objects for dynamic selection
#     all_agents = {
#         "UserProxyAgent": user_proxy,
#         "DecisionOrchestrator": decision_orchestrator,
#         "ChannelAgent": channel_agent,
#         "DamageAnalyzer": damage_analyzer,
#         "EntitlementAnalyzer": entitlement_analyzer
#     }

#     # Test scenario
#     scenario = """Scenario details:
# 1. Service Tag: AXBYCZ6
# 2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
# 3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
# 4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days - so AD WO cannot be created
# 5. VL Model Output: VL Model did not find any image or format is invalid
# 6. Region: Australia
# 7. Damage Description: dropped the system"""

#     # Select agents based on scenario
#     selected_agent_names = select_agents(scenario)
#     selected_agents = [all_agents[name] for name in selected_agent_names]

#     logging.info(f"Selected agent names: {selected_agent_names}")

#     # Configure group chat with selected agents
#     group_chat = GroupChat(
#         agents=selected_agents,
#         max_round=5,
#         speaker_selection_method="Auto",
#         allow_repeat_speaker=False,
        
        
#     )

#     # Define termination condition
#     def is_termination_msg(message):
#         logging.info(f"Checking termination message: {message}")
#         return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]

#     # Create GroupChatManager with strict routing
#     manager = GroupChatManager(
#         groupchat=group_chat,
#         llm_config=llm_config,
# system_message = """You are the GroupChatManager. You are NOT making decisions or analyzing data. Your only job is to route messages between agents according to strict rules below.

# ### RULES
# 1. ALWAYS start with @UserProxyAgent.
# 2. After @UserProxyAgent:
#    - If message contains any of these phrases:
#      - "no image"
#      - "not found"
#      - "invalid format"
#      - "format invalid"
#      - "did not find any image"
#      - "did not detect any image"
#    → Next speaker: @ChannelAgent
# 3. After @ChannelAgent → Next speaker: @DecisionOrchestrator
# 4. After @DecisionOrchestrator → TERMINATE
# 5. NEVER skip any agent in this sequence.

# ### OUTPUT FORMAT
# Next speaker: @AgentName
# Reason: [Why you chose this agent]

# DO NOT write anything else.

# ### SPECIAL INSTRUCTIONS FOR LLAMA3.1
# - Be deterministic.
# - Match keywords exactly.
# - Never infer intent beyond trigger phrases.
# - Always follow step-by-step logic.
# """,
#         is_termination_msg=is_termination_msg
#     )

#     # Initiate chat
#     chat_result = user_proxy.initiate_chat(
#         manager,
#         message=scenario,
#         silent=False
#     )

#     # Extract and display final decision
#     final_message = None
#     for msg in reversed(chat_result.chat_history):
#         if msg.get('name') == 'DescisionOrchestrator':
#             final_message = msg['content']
#             break

#     if final_message:
#         print("\n=== FINAL DECISION ===")
#         print(final_message)
#         print("======================")
#     else:
#         print("No final decision was generated by the decision_orchestrator.")

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
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# def prepare_initial_message(scenario_text, force_speaker=None):
#     """Inject forced speaker instruction into message."""
#     if force_speaker:
#         return scenario_text + f"\n\nNext speaker: {force_speaker}"
#     return scenario_text

# def select_agents(scenario_message):
#     """Select appropriate agents based on VL Model Output."""
#     vl_model_output = ""
#     for line in scenario_message.split('\n'):
#         if "VL Model Output:" in line:
#             vl_model_output = line.split(":")[1].strip().lower()

#     trigger_phrases = ["no image", "not found", "invalid format", "format invalid",
#                        "did not find any image", "did not detect any image"]

#     if any(phrase in vl_model_output for phrase in trigger_phrases):
#         return ["UserProxyAgent", "ChannelAgent", "DecisionOrchestrator"]
#     else:
#         return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "DecisionOrchestrator"]

# def main():
#     # Create agents
#     user_proxy = create_user_proxy(llm_config)
#     decision_orchestrator = create_decision_orchestrator(llm_config)
#     channel_agent = create_channel_agent(llm_config)
#     damage_analyzer = create_damage_analyzer(llm_config)
#     entitlement_analyzer = create_entitlement_analyzer(llm_config)

#     all_agents = {
#         "UserProxyAgent": user_proxy,
#         "DecisionOrchestrator": decision_orchestrator,
#         "ChannelAgent": channel_agent,
#         "DamageAnalyzer": damage_analyzer,
#         "EntitlementAnalyzer": entitlement_analyzer
#     }

#     # Test scenario
#     scenario = """Scenario details:
# 1. Service Tag: AXBYCZ6
# 2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
# 3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
# 4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days - so AD WO cannot be created
# 5. VL Model Output: VL Model did not find any image or format is invalid
# 6. Region: Australia
# 7. Damage Description: dropped the system"""

#     selected_agent_names = select_agents(scenario)
#     selected_agents_list = [all_agents[name] for name in selected_agent_names]

#     print("Selected Agents:", selected_agent_names)

#     # Force ChannelAgent to speak next if needed
#     force_speaker = "@ChannelAgent" if "ChannelAgent" in selected_agent_names else None
#     final_message = prepare_initial_message(scenario, force_speaker)

#     group_chat = GroupChat(
#         agents=selected_agents_list,
#         messages=[],
#         max_round=10,
#         speaker_selection_method="auto",
#         allow_repeat_speaker=False
#     )

#     group_chat_manager_prompt = """You are the GroupChatManager. You do NOT make decisions or analyze data.

# ### RULES
# - If the input contains "Next speaker: @AgentName", you MUST output:
#   Next speaker: @AgentName
#   Reason: Forced by external trigger
# - Otherwise, route based on content using strict keyword matching.

# ### OUTPUT FORMAT
# Next speaker: @AgentName
# Reason: [Why this agent was selected]

# DO NOT write anything else."""

#     manager = GroupChatManager(
#         groupchat=group_chat,
#         llm_config=llm_config,
#         system_message=group_chat_manager_prompt,
#         is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "")
#     )

#     # Start chat
#     chat_result = user_proxy.initiate_chat(
#         manager,
#         message=final_message,
#         silent=False
#     )

#     # Print final decision
#     final_message = None
#     for msg in reversed(chat_result.chat_history):
#         if msg.get('name') == 'DecisionOrchestrator':
#             final_message = msg['content']
#             break

#     if final_message:
#         print("\n=== FINAL DECISION ===")
#         print(final_message)
#         print("======================")
#     else:
#         print("No final decision was generated.")

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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def select_agents(scenario_message):
    """
    Selects agents based on the VL Model Output in the scenario.
    Returns a list of agent names for the appropriate scenario.
    """
    vl_model_output = ""
    for line in scenario_message.split('\n'):
        if "VL Model Output:" in line:
            vl_model_output = line.split(":")[1].strip().lower()

    trigger_phrases = [
        "no image", "not found", "invalid format", "format invalid",
        "did not find any image", "did not detect any image"
    ]

    if any(phrase in vl_model_output for phrase in trigger_phrases):
        return ["UserProxyAgent", "ChannelAgent", "DecisionOrchestrator"]
    else:
        return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "DecisionOrchestrator"]

def custom_speaker_selection_func(last_speaker, groupchat):
    messages = groupchat.messages

    # Initial message from UserProxyAgent
    if last_speaker is user_proxy:
        # Extract VL Model Output
        vl_output_found = False
        for msg in reversed(messages):
            if "VL Model Output:" in msg.get("content", ""):
                vl_content = msg["content"].lower()
                trigger_phrases = [
                    "no image", "not found", "invalid format", "format invalid",
                    "did not find any image", "did not detect any image"
                ]
                if any(trigger in vl_content for trigger in trigger_phrases):
                    vl_output_found = True
                break

        if vl_output_found:
            return channel_agent
        else:
            return entitlement_analyzer

    elif last_speaker is channel_agent:
        return decision_orchestrator

    elif last_speaker is entitlement_analyzer:
        return damage_analyzer

    elif last_speaker is damage_analyzer:
        return decision_orchestrator

    elif last_speaker is decision_orchestrator:
        return "FINISH"

    else:
        return None

def main():
    # Create agents
    global user_proxy, channel_agent, decision_orchestrator, damage_analyzer, entitlement_analyzer

    user_proxy = create_user_proxy(llm_config)
    decision_orchestrator = create_decision_orchestrator(llm_config)
    channel_agent = create_channel_agent(llm_config)
    damage_analyzer = create_damage_analyzer(llm_config)
    entitlement_analyzer = create_entitlement_analyzer(llm_config)

    all_agents = {
        "UserProxyAgent": user_proxy,
        "ChannelAgent": channel_agent,
        "DecisionOrchestrator": decision_orchestrator,
        "DamageAnalyzer": damage_analyzer,
        "EntitlementAnalyzer": entitlement_analyzer
    }

    # Test scenario
    scenario = """Scenario details:
1. Service Tag: AXBYCZ6
2. AD Entitlement: Service Tag has entitlement for Accidental damage or the same expired
3. AD Incident Available: Service Tag has incident available so a Work Order for AD can be created
4. AD Cooling Period: Service Tag is outside of cooling off period of 30 days - so AD WO cannot be created
5. VL Model Output: VL Model did not find any image or format is invalid
6. Region: Australia
7. Damage Description: dropped the system"""

    selected_agent_names = select_agents(scenario)
    selected_agents_list = [all_agents[name] for name in selected_agent_names]

    print("Selected Agents:", selected_agent_names)

    group_chat = GroupChat(
        agents=selected_agents_list,
        messages=[],
        max_round=10,
        speaker_selection_method=custom_speaker_selection_func,
        allow_repeat_speaker=False
    )

    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        system_message="You are the GroupChatManager. You coordinate conversations between agents.",
        is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "")
    )

    # Start chat
    chat_result = user_proxy.initiate_chat(
        manager,
        message=scenario,
        silent=False
    )

    # Print final decision
    final_message = None
    for msg in reversed(chat_result.chat_history):
        if msg.get('name') == 'DecisionOrchestrator':
            final_message = msg['content']
            break

    if final_message:
        print("\n=== FINAL DECISION ===")
        print(final_message)
        print("======================")
    else:
        print("No final decision was generated.")

if __name__ == "__main__":
    main()