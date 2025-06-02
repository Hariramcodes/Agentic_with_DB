import logging
import asyncio
from autogen import GroupChat
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
        # Define user input for testing different regions
        user_input = {
            "service_tag": "AXBYCZ6",
            "region": "France",  # Try changing to: Germany, USA, UK, India, China, Japan, Australia
            "vl_model_output": "No image data available"
        }

        logger.info(f"Testing with region: {user_input['region']}")

        # Create agents
        user_proxy = create_user_proxy(llm_config)
        channel_agent = create_channel_agent(llm_config, "ChannelAgent")
        retrieval_agent = create_retrieval_agent(llm_config, "ChannelAgent")
        decision_orchestrator = create_decision_orchestrator(llm_config)

        # Create group chat without speaker transitions (using auto selection)
        group_chat = GroupChat(
            agents=[user_proxy, channel_agent, retrieval_agent, decision_orchestrator],
            messages=[],
            max_round=15,  # Increased to allow for proper flow
            speaker_selection_method="auto"
        )

        # Create group chat manager
        group_chat_manager = create_group_chat_manager(group_chat, llm_config)

        # Create initial message in the expected format
        initial_message = f"""Please process this Dell support request:

Service Tag: {user_input['service_tag']}
Region: {user_input['region']}  
VL Model Output: {user_input['vl_model_output']}

Please provide appropriate support instructions for this customer."""

        logger.info("Starting group chat with UserProxyAgent")
        logger.info(f"Initial message: {initial_message}")

        # Initiate chat
        result = await user_proxy.a_initiate_chat(
            group_chat_manager,
            message=initial_message,
            max_turns=15
        )

        logger.info("Group chat completed successfully")
        
        # Print final conversation summary
        if group_chat.messages:
            logger.info("\n" + "="*50 + " CONVERSATION SUMMARY " + "="*50)
            for i, msg in enumerate(group_chat.messages[-5:], 1):  # Show last 5 messages
                speaker = msg.get('name', 'Unknown')
                content = msg.get('content', '')[:200] + "..." if len(msg.get('content', '')) > 200 else msg.get('content', '')
                logger.info(f"{i}. {speaker}: {content}")
            logger.info("="*117)

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())