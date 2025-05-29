import logging
import asyncio
from autogen import GroupChat, GroupChatManager
from agents.user_proxy import create_user_proxy
from agents.channel_agent import create_channel_agent
from agents.retrieval_agent import create_retrieval_agent
from agents.decision_orchestrator import create_decision_orchestrator
from agents.group_chat_manager import create_group_chat_manager
from config.llm_config import llm_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Define user input
        user_input = {
            "service_tag": "AXBYCZ6",
            "region": "France",
            "vl_model_output": "No image data available"
        }

        # Create agents
        user_proxy = create_user_proxy(llm_config)
        channel_agent = create_channel_agent(llm_config, "ChannelAgent")
        retrieval_agent = create_retrieval_agent(llm_config, "ChannelAgent")
        decision_orchestrator = create_decision_orchestrator(llm_config)

        # Define allowed speaker transitions
        allowed_transitions = {
            user_proxy: [channel_agent],
            channel_agent: [retrieval_agent, decision_orchestrator],
            retrieval_agent: [channel_agent],
            decision_orchestrator: [user_proxy]
        }

        # Create group chat
        group_chat = GroupChat(
            agents=[user_proxy, channel_agent, retrieval_agent, decision_orchestrator],
            messages=[],
            max_round=10,
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            speaker_transitions_type="allowed"
        )

        # Create group chat manager
        group_chat_manager = create_group_chat_manager(group_chat, llm_config)

        # Initiate chat
        initial_message = f"""@ChannelAgent: Please provide image upload instructions:
Service Tag: {user_input['service_tag']}
Region: {user_input['region']}
VL Model Output: {user_input['vl_model_output']}"""

        logger.info("Starting group chat")
        await user_proxy.a_initiate_chat(
            group_chat_manager,
            message=initial_message
        )

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())