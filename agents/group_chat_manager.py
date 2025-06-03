from autogen import GroupChatManager
import logging

logger = logging.getLogger(__name__)

def create_group_chat_manager(group_chat, llm_config):
    """Create a GroupChatManager with custom speaker selection logic"""
    
    def custom_select_speaker(last_speaker, groupchat):
        """Custom speaker selection function for the conversation flow"""
        try:
            messages = groupchat.messages
            logger.info(f"Speaker selection: last={last_speaker.name if last_speaker else 'None'}, total_messages={len(messages)}")

            # Handle start of conversation
            if not messages or len(messages) == 1:
                # First message is from UserProxy, next should also be UserProxy to process it
                user_proxy = next((agent for agent in groupchat.agents if agent.name == "UserProxyAgent"), None)
                logger.info("Starting conversation - selecting UserProxyAgent")
                return user_proxy

            last_message_content = messages[-1].get("content", "")
            logger.info(f"Last message preview: {last_message_content[:100]}...")
            
            # Check for termination
            if "TERMINATE" in last_message_content:
                logger.info("TERMINATE found, ending conversation")
                return None

            # Speaker selection logic
            if last_speaker and last_speaker.name == "UserProxyAgent":
                # Check if UserProxy has processed the input (sent the VL_STATUS message)
                if "VL_STATUS: NO_IMAGE_FOUND" in last_message_content:
                    # UserProxy processed input -> ChannelAgent
                    channel_agent = next((agent for agent in groupchat.agents if agent.name == "ChannelAgent"), None)
                    logger.info("UserProxy processed input → ChannelAgent")
                    return channel_agent
                else:
                    # UserProxy hasn't processed yet, let it continue
                    logger.info("UserProxy hasn't processed input yet, continuing with UserProxy")
                    return last_speaker

            elif last_speaker and last_speaker.name == "ChannelAgent":
                # Check if ChannelAgent is requesting retrieval or providing final response
                if "RetrievalAgent:" in last_message_content and "Fetch chunks" in last_message_content:
                    # ChannelAgent requesting chunks -> RetrievalAgent
                    retrieval_agent = next((agent for agent in groupchat.agents if "RetrievalAgent" in agent.name), None)
                    logger.info("ChannelAgent → RetrievalAgent (requesting chunks)")
                    return retrieval_agent
                elif "Upload Instructions:" in last_message_content and "Documents Consulted:" in last_message_content:
                    # ChannelAgent providing final response -> DecisionOrchestrator
                    decision_agent = next((agent for agent in groupchat.agents if agent.name == "DecisionOrchestrator"), None)
                    logger.info("ChannelAgent → DecisionOrchestrator (final response)")
                    return decision_agent
                else:
                    logger.warning(f"ChannelAgent message doesn't match expected patterns")
                    return None

            elif last_speaker and "RetrievalAgent" in last_speaker.name:
                # After RetrievalAgent, always back to ChannelAgent for processing
                if "Retrieved chunks:" in last_message_content:
                    channel_agent = next((agent for agent in groupchat.agents if agent.name == "ChannelAgent"), None)
                    logger.info("RetrievalAgent → ChannelAgent (chunks returned for processing)")
                    return channel_agent
                else:
                    logger.warning(f"RetrievalAgent response doesn't contain expected chunks")
                    return None

            elif last_speaker and last_speaker.name == "DecisionOrchestrator":
                # DecisionOrchestrator is final - end conversation
                logger.info("DecisionOrchestrator finished - ending conversation")
                return None

            else:
                # Unexpected flow - end conversation
                logger.warning(f"Unexpected speaker: {last_speaker.name if last_speaker else 'None'}")
                return None

        except Exception as e:
            logger.error(f"Exception in speaker selection: {str(e)}")
            return None

    # Set the group chat to use manual speaker selection with our custom function
    group_chat.speaker_selection_method = "manual"
    group_chat.speaker_selection_function = custom_select_speaker
    
    # Create the GroupChatManager
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="""You are the GroupChatManager for Dell's technical support workflow.

**Expected Flow**:
1. UserProxyAgent: Process input and identify NO_IMAGE_FOUND scenario
2. ChannelAgent: Request retrieval for upload instructions  
3. RetrievalAgent: Return raw chunks from vector database
4. ChannelAgent: Process chunks and provide upload instructions
5. DecisionOrchestrator: Create final report and TERMINATE

**Guidelines**:
- Let each agent complete their specific task
- ChannelAgent should process and summarize the retrieved chunks
- RetrievalAgent only returns raw chunks, no processing
- Ensure proper termination with TERMINATE signal"""
    )
    
    logger.info("Created GroupChatManager with custom speaker selection and system message")
    return manager