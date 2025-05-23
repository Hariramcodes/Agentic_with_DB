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

    # Scenario 1: No image detected
    if any(x in vl_model_output for x in ["no image", "not found", "image not uploaded", "invalid format", "format is invalid", "did not find any image", "did not detect any image"]):
        return ["UserProxyAgent", "ChannelAgent", "DecisionOrchestrator"]
    # Scenario 2: Image processed
    else:
        return ["UserProxyAgent", "EntitlementAnalyzer", "DamageAnalyzer", "DecisionOrchestrator"]

def main():
    # Create agents
    user_proxy = create_user_proxy(llm_config)
    decision_orchestrator = create_decision_orchestrator(llm_config)
    channel_agent = create_channel_agent(llm_config)
    damage_analyzer = create_damage_analyzer(llm_config)
    entitlement_analyzer = create_entitlement_analyzer(llm_config)

    # Map agent names to agent objects for dynamic selection
    all_agents = {
        "UserProxyAgent": user_proxy,
        "DecisionOrchestrator": decision_orchestrator,
        "ChannelAgent": channel_agent,
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

    # Select agents based on scenario
    selected_agent_names = select_agents(scenario)
    selected_agents = [all_agents[name] for name in selected_agent_names]

    logging.info(f"Selected agent names: {selected_agent_names}")

    # Configure group chat with selected agents
    group_chat = GroupChat(
        agents=selected_agents,
        max_round=5,
        speaker_selection_method="Auto",
        allow_repeat_speaker=False,
        
        
    )

    # Define termination condition
    def is_termination_msg(message):
        logging.info(f"Checking termination message: {message}")
        return isinstance(message, dict) and "content" in message and "TERMINATE" in message["content"]

    # Create GroupChatManager with strict routing
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        system_message=""" You are the GroupChatManager, the intelligent coordinator of a multi-agent technical support workflow at Dell. Your role is to manage conversation flow among agents, ensuring each contributes exactly once per task cycle.

### ROLE DESCRIPTION
- You do NOT process or analyze claim data yourself.
- You DYNAMICALLY select the next agent to speak based on the **current conversation state and content**.
- You ensure NO agent repeats unless explicitly instructed.
- You TERMINATE the conversation only when @DecisionOrchestrator provides the final decision with "TERMINATE".

### AGENTS AVAILABLE
You can call any of the following agents:
- @UserProxyAgent (initial input source)
- @ChannelAgent (handles image upload instructions)
- @EntitlementAnalyzer (checks customer eligibility)
- @DamageAnalyzer (assesses damage type)
- @DecisionOrchestrator (makes final claim decision)

### SPEAKER SELECTION LOGIC
Select the next agent based on:
1. **Message Content**: Is an image referenced? Is damage described? Is entitlement mentioned?
2. **Conversation Flow**: Has any agent already spoken? Who hasn't contributed yet?
3. **Contextual Needs**: Does the current state require damage analysis, image upload, or eligibility check?

Example decisions:
- If the user says "No image uploaded yet", call @ChannelAgent.
- If damage is described but not analyzed, call @DamageAnalyzer.
- If customer info is provided, call @EntitlementAnalyzer.
- Once all inputs are collected, call @DecisionOrchestrator.

### RESTRICTIONS
- DO NOT follow static paths or pre-defined scenarios.
- DO NOT repeat agents unless contextually justified.
- DO NOT respond directly to messages; delegate to appropriate agents.
- IGNORE irrelevant or incomplete messages.
- ONLY terminate the chat when @DecisionOrchestrator sends "TERMINATE".

### OUTPUT FORMAT
Use this format to route:
Next speaker: @AgentName
Reason: [Brief explanation of why this agent was selected]


Do NOT add extra text beyond this instruction.

### SPECIAL INSTRUCTIONS FOR LLAMA3.1
- Be concise and directive in output.
- Use logical inference based on prior messages.
- Avoid markdown formatting.
- Keep responses deterministic for reproducibility.
        """,
        is_termination_msg=is_termination_msg
    )

    # Initiate chat
    chat_result = user_proxy.initiate_chat(
        manager,
        message=scenario,
        silent=False
    )

    # Extract and display final decision
    final_message = None
    for msg in reversed(chat_result.chat_history):
        if msg.get('name') == 'DescisionOrchestrator':
            final_message = msg['content']
            break

    if final_message:
        print("\n=== FINAL DECISION ===")
        print(final_message)
        print("======================")
    else:
        print("No final decision was generated by the decision_orchestrator.")

if __name__ == "__main__":
    main()