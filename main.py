from autogen import GroupChat
import asyncio
import logging
from agents.channel_agent import create_channel_agent
from agents.user_proxy import create_user_proxy
from agents.group_chat_manager import create_group_chat_manager
from agents.decision_orchestrator import create_decision_orchestrator
from agents.retrieval_agent import create_retrieval_agent
from config.llm_config import llm_config

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Initialize agents
        user_proxy = create_user_proxy(llm_config)
        channel_agent = create_channel_agent(llm_config)
        retrieval_agent = create_retrieval_agent(llm_config, "ChannelAgent")
        decision_orchestrator = create_decision_orchestrator(llm_config)
        
        # Create group chat
        group_chat = GroupChat(
            agents=[user_proxy, channel_agent, retrieval_agent, decision_orchestrator],
            messages=[],
            max_round=10
        )
        group_chat_manager = create_group_chat_manager(group_chat, llm_config)

        # Start workflow
        user_input = {
            "service_tag": "AXBYCZ6",
            "region": "France",
            "vl_model_output": "No image data available"
        }
        prompt = f"""
        @ChannelAgent: Please provide image upload instructions:
        Service Tag: {user_input['service_tag']}
        Region: {user_input['region']}
        VL Model Output: {user_input['vl_model_output']}
        """
        logger.info("Initiating workflow with user input")
        chat_result = user_proxy.initiate_chat(
            group_chat_manager,
            message=prompt
        )
        if any("TERMINATE" in msg.get("content", "") for msg in chat_result.chat_history):
            logger.info("Workflow terminated successfully")
        else:
            logger.warning("Workflow did not terminate properly")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())