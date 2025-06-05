from autogen import GroupChatManager
import logging

logger = logging.getLogger(__name__)

def custom_select_speaker(last_speaker, groupchat):
    """Custom speaker selection function for automatic flow"""
    try:
        messages = groupchat.messages
        
        # Debug: Print everything
        print(f"\n🔍 DEBUG: Auto Speaker Selection")
        print(f"   Last speaker: {last_speaker.name if last_speaker else 'None'}")
        print(f"   Total messages: {len(messages)}")
        print(f"   Available agents: {[agent.name for agent in groupchat.agents]}")
        
        if messages:
            last_message_content = messages[-1].get('content', '')
            print(f"   Last message (first 100 chars): {last_message_content[:100]}...")
        else:
            last_message_content = ''
        
        # Handle start of conversation
        if not messages or len(messages) == 1:
            user_proxy = next((agent for agent in groupchat.agents if agent.name == "UserProxyAgent"), None)
            print(f"   ✅ START: Selecting UserProxy: {user_proxy.name if user_proxy else 'None'}")
            return user_proxy
            
        # Handle UserProxy responses
        if last_speaker and last_speaker.name == "UserProxyAgent":
            if "VL_STATUS: NO_IMAGE_FOUND" in last_message_content:
                channel_agent = next((agent for agent in groupchat.agents if agent.name == "ChannelAgent"), None)
                print(f"   ✅ UserProxy → ChannelAgent: {channel_agent.name if channel_agent else 'None'}")
                return channel_agent
            else:
                print(f"   🔄 UserProxy continues")
                return last_speaker
        
        # Handle ChannelAgent responses
        if last_speaker and last_speaker.name == "ChannelAgent":
            print(f"🎯 ChannelAgent just spoke")
            print(f"   Checking for '@ChannelAgent_RetrievalAgent:' in message...")
            print(f"   Found: {'@ChannelAgent_RetrievalAgent:' in last_message_content}")
            
            if "@ChannelAgent_RetrievalAgent:" in last_message_content:
                # Find retrieval agent
                retrieval_agents = [agent for agent in groupchat.agents if "RetrievalAgent" in agent.name]
                print(f"   🔍 Found RetrievalAgents: {[agent.name for agent in retrieval_agents]}")
                
                if retrieval_agents:
                    selected = retrieval_agents[0]
                    print(f"   ✅ SELECTED: {selected.name}")
                    return selected
                else:
                    print(f"   ❌ NO RETRIEVAL AGENT FOUND!")
                    return None
            elif "Upload Instructions:" in last_message_content:
                # ChannelAgent provided final response -> DecisionOrchestrator
                decision_agent = next((agent for agent in groupchat.agents if agent.name == "DecisionOrchestrator"), None)
                print(f"   ✅ ChannelAgent → DecisionOrchestrator: {decision_agent.name if decision_agent else 'None'}")
                return decision_agent
            else:
                print(f"   ❌ ChannelAgent message doesn't match patterns")
                return None
        
        # Handle RetrievalAgent responses
        if last_speaker and "RetrievalAgent" in last_speaker.name:
            channel_agent = next((agent for agent in groupchat.agents if agent.name == "ChannelAgent"), None)
            print(f"   ✅ RetrievalAgent → ChannelAgent: {channel_agent.name if channel_agent else 'None'}")
            return channel_agent
            
        # Handle DecisionOrchestrator
        if last_speaker and last_speaker.name == "DecisionOrchestrator":
            print(f"   ✅ DecisionOrchestrator spoke - ENDING CONVERSATION")
            return None
                
        print(f"   ❌ No pattern matched, ending conversation")
        return None
        
    except Exception as e:
        print(f"❌ ERROR in speaker selection: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def create_group_chat_manager(groupchat, llm_config):
    """Create GroupChatManager with custom speaker selection"""
    
    # IMPORTANT: Set the custom speaker selection on the groupchat BEFORE creating manager
    groupchat.speaker_selection_method = custom_select_speaker
    
    # Create the REAL GroupChatManager (not ConversableAgent)
    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
        name="chat_manager",
        system_message="""You are the GroupChatManager for Dell's technical support workflow. 
        You manage the conversation flow between specialized agents.
        
        Your role is to:
        - Ensure the correct agent speaks at the right time
        - Keep the conversation focused on solving the customer's issue
        - Coordinate between UserProxy, ChannelAgent, RetrievalAgent, and DecisionOrchestrator
        
        Do not generate content yourself - let the specialized agents handle their tasks.""",
    )
    
    logger.info("Created GroupChatManager with CUSTOM speaker selection and system message")
    
    return manager