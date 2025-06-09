from autogen import GroupChatManager, GroupChat
import logging
import re

logger = logging.getLogger(__name__)

def custom_speaker_selection_func(last_speaker, groupchat):
    """Custom speaker selection function with programmatic logic"""
    
    if not groupchat.messages:
        return groupchat.agents[0]  # Start with first agent (UserProxyAgent)
    
    last_message = groupchat.messages[-1]["content"]
    last_speaker_name = last_speaker.name if last_speaker else None
    
    print(f"🎯 Custom Speaker Selection:")
    print(f"   Last speaker: {last_speaker_name}")
    print(f"   Last message preview: {last_message[:100]}...")
    
    # RULE 1: Detect retrieval requests programmatically
    retrieval_patterns = {
        "@ChannelAgent_RetrievalAgent:": "ChannelAgent_RetrievalAgent",
        "@EntitlementAnalyzer_RetrievalAgent:": "EntitlementAnalyzer_RetrievalAgent", 
        "@DamageAnalyzer_RetrievalAgent:": "DamageAnalyzer_RetrievalAgent"
    }
    
    for pattern, agent_name in retrieval_patterns.items():
        if pattern in last_message:
            for agent in groupchat.agents:
                if agent.name == agent_name:
                    print(f"   ✅ RETRIEVAL DETECTED: {pattern} → Selecting {agent_name}")
                    return agent
    
    # RULE 2: VL_STATUS routing
    if last_speaker_name == "UserProxyAgent":
        if "VL_STATUS: NO_IMAGE_FOUND" in last_message:
            for agent in groupchat.agents:
                if agent.name == "ChannelAgent":
                    print(f"   ✅ VL_STATUS: NO_IMAGE_FOUND → Selecting ChannelAgent")
                    return agent
        elif "VL_STATUS: IMAGE_FOUND" in last_message:
            for agent in groupchat.agents:
                if agent.name == "EntitlementAnalyzer":
                    print(f"   ✅ VL_STATUS: IMAGE_FOUND → Selecting EntitlementAnalyzer")
                    return agent
    
    # RULE 3: After retrieval agents
    retrieval_to_main = {
        "ChannelAgent_RetrievalAgent": "ChannelAgent",
        "EntitlementAnalyzer_RetrievalAgent": "EntitlementAnalyzer",
        "DamageAnalyzer_RetrievalAgent": "DamageAnalyzer"
    }
    
    if last_speaker_name in retrieval_to_main:
        target_agent = retrieval_to_main[last_speaker_name]
        for agent in groupchat.agents:
            if agent.name == target_agent:
                print(f"   ✅ After retrieval → Selecting {target_agent}")
                return agent
    
    # RULE 4: Workflow completion
    if last_speaker_name == "ChannelAgent" and ("ANALYSIS COMPLETE" in last_message or len(last_message) > 200):
        for agent in groupchat.agents:
            if agent.name == "DecisionOrchestrator":
                print(f"   ✅ ChannelAgent complete → Selecting DecisionOrchestrator")
                return agent
                
    if last_speaker_name == "EntitlementAnalyzer" and "ENTITLEMENT ANALYSIS COMPLETE" in last_message:
        for agent in groupchat.agents:
            if agent.name == "DamageAnalyzer":
                print(f"   ✅ EntitlementAnalyzer complete → Selecting DamageAnalyzer")
                return agent
                
    if last_speaker_name == "DamageAnalyzer" and "DAMAGE ANALYSIS COMPLETE" in last_message:
        for agent in groupchat.agents:
            if agent.name == "DecisionOrchestrator":
                print(f"   ✅ DamageAnalyzer complete → Selecting DecisionOrchestrator")
                return agent
    
    # RULE 5: Default fallback
    print(f"   ⚠️  No specific rule matched, using fallback logic")
    
    # If UserProxyAgent just passed through scenario without analysis, select it again
    if last_speaker_name == "UserProxyAgent" and "Scenario details:" in last_message and "VL_STATUS:" not in last_message:
        print(f"   ↻ UserProxyAgent needs to analyze → Selecting UserProxyAgent again")
        return last_speaker
    
    # Default: select next agent in sequence
    try:
        current_index = groupchat.agents.index(last_speaker)
        next_agent = groupchat.agents[(current_index + 1) % len(groupchat.agents)]
        print(f"   → Default next: {next_agent.name}")
        return next_agent
    except:
        print(f"   → Fallback: {groupchat.agents[0].name}")
        return groupchat.agents[0]


class CustomGroupChatManager(GroupChatManager):
    def __init__(self, groupchat, llm_config=None):
        super().__init__(
            groupchat=groupchat, 
            llm_config=llm_config,
            max_consecutive_auto_reply=30,
            human_input_mode="NEVER",
            is_termination_msg=lambda x: False
        )
        logger.info("Created CustomGroupChatManager with programmatic speaker selection")


def create_group_chat_manager(agents, llm_config):
    """Create group chat manager with custom speaker selection"""
    
    print(f"🔧 Creating GroupChat with CUSTOM programmatic speaker selection")
    print(f"   👥 Agents: {[agent.name for agent in agents]}")
    print(f"   🎯 Expected: UserProxy → ChannelAgent → ChannelAgent_RetrievalAgent → ChannelAgent → DecisionOrchestrator")
    
    logger.info(f"✅ Agent list: {[agent.name for agent in agents]}")
    
    # Create groupchat with custom speaker selection function
    groupchat = GroupChat(
        agents=agents,
        messages=[],
        max_round=40,
        speaker_selection_method=custom_speaker_selection_func,  # Use custom function
        allow_repeat_speaker=True,
        max_retries_for_selecting_speaker=1,
        enable_clear_history=False
    )
    
    manager = CustomGroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config
    )
    
    print(f"   ✅ GroupChat configured with PROGRAMMATIC speaker selection")
    print(f"   ✅ Focus: 100% reliable retrieval detection")
    
    return manager