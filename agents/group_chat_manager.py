from autogen import GroupChatManager
import logging

logger = logging.getLogger(__name__)

def create_group_chat_manager(group_chat, llm_config):
    def custom_select_speaker(self, last_speaker, groupchat):
        try:
            messages = groupchat.messages
            logger.info(f"Custom speaker selection: last_speaker={last_speaker.name}, total_messages={len(messages)}")

            if not messages:
                logger.info("No messages, selecting first agent")
                return groupchat.agents[0]

            last_message_content = messages[-1].get("content", "")
            logger.info(f"Last message content preview: {last_message_content[:200]}...")

            # Check for termination first
            if "TERMINATE" in last_message_content:
                logger.info("TERMINATE found, ending conversation")
                return None

            # Agent selection logic based on message content and speaker
            if last_speaker.name == "UserProxyAgent":
                # UserProxy always goes to ChannelAgent
                channel_agent = next((agent for agent in groupchat.agents if agent.name == "ChannelAgent"), None)
                logger.info(f"After UserProxy, selecting ChannelAgent")
                return channel_agent

            elif last_speaker.name == "ChannelAgent":
                # Check if ChannelAgent is requesting chunks or providing final response
                if "@ChannelAgent_RetrievalAgent:" in last_message_content:
                    # ChannelAgent requesting chunks -> RetrievalAgent
                    retrieval_agent = next((agent for agent in groupchat.agents if "RetrievalAgent" in agent.name), None)
                    logger.info(f"ChannelAgent requesting chunks, selecting RetrievalAgent")
                    return retrieval_agent
                elif "@GroupChatManager:" in last_message_content and "Upload Instructions:" in last_message_content:
                    # ChannelAgent providing final response -> DecisionOrchestrator
                    decision_agent = next((agent for agent in groupchat.agents if agent.name == "DecisionOrchestrator"), None)
                    logger.info(f"ChannelAgent providing final response, selecting DecisionOrchestrator")
                    return decision_agent
                else:
                    logger.warning(f"ChannelAgent response doesn't match expected format")
                    return None

            elif "RetrievalAgent" in last_speaker.name:
                # RetrievalAgent always goes back to ChannelAgent
                if "@ChannelAgent: Retrieved chunks:" in last_message_content:
                    channel_agent = next((agent for agent in groupchat.agents if agent.name == "ChannelAgent"), None)
                    logger.info(f"RetrievalAgent returned chunks, back to ChannelAgent")
                    return channel_agent
                else:
                    logger.warning(f"RetrievalAgent response doesn't contain expected chunks")
                    return None

            elif last_speaker.name == "DecisionOrchestrator":
                # DecisionOrchestrator should terminate
                logger.info("DecisionOrchestrator spoke, conversation should end")
                return None.name == "DecisionOrchestrator"
                # DecisionOrchestrator should be the last to speak
                logger.info("DecisionOrchestrator spoke, conversation should end")
                return None

            # Default fallback
            logger.warning("No specific speaker selection rule matched, ending conversation")
            return None

        except Exception as e:
            logger.error(f"Error in custom_select_speaker: {str(e)}")
            return None

    # Create GroupChatManager
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False
    )

    # Override select_speaker method
    manager.select_speaker = custom_select_speaker.__get__(manager, GroupChatManager)

    # Override generate_reply to handle the conversation flow
    original_generate_reply = manager.generate_reply

    def custom_generate_reply(self, messages=None, sender=None, config=None):
        try:
            # Check for termination in the last message
            if messages and len(messages) > 0:
                last_content = messages[-1].get("content", "")
                if "TERMINATE" in last_content:
                    logger.info("TERMINATE detected in generate_reply, ending conversation")
                    return "Conversation terminated successfully."

            # Use original generate_reply
            return original_generate_reply(messages, sender, config)
        except Exception as e:
            logger.error(f"Error in custom_generate_reply: {str(e)}")
            return f"Error in conversation: {str(e)}"

    manager.generate_reply = custom_generate_reply.__get__(manager, GroupChatManager)

    return manager