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
        # Test case
        user_input = {
            "service_tag": "AXBYCZ6",
            "region": "France",
            "vl_model_output": "No image data available"
        }

        logger.info(f"Testing with region: {user_input['region']}")
        logger.info(f"Service Tag: {user_input['service_tag']}")
        logger.info(f"VL Output: {user_input['vl_model_output']}")

        # Create agents
        logger.info("Creating agents...")
        user_proxy = create_user_proxy(llm_config)
        channel_agent = create_channel_agent(llm_config, "ChannelAgent")
        retrieval_agent = create_retrieval_agent(llm_config, "ChannelAgent")
        decision_orchestrator = create_decision_orchestrator(llm_config)

        # Create group chat with manual speaker selection
        logger.info("Creating group chat...")
        group_chat = GroupChat(
            agents=[user_proxy, channel_agent, retrieval_agent, decision_orchestrator],
            messages=[],
            max_round=8,
            speaker_selection_method="manual"  # Will be set by group_chat_manager
        )

        # Create group chat manager with custom speaker selection
        logger.info("Creating group chat manager...")
        group_chat_manager = create_group_chat_manager(group_chat, llm_config)

        # Create initial message
        initial_message = f"""Service Tag: {user_input['service_tag']}
Region: {user_input['region']}
VL Model Output: {user_input['vl_model_output']}"""

        logger.info("="*60)
        logger.info("STARTING DELL SUPPORT CONVERSATION")
        logger.info("="*60)
        logger.info(f"Initial message: {initial_message}")
        logger.info("")

        try:
            # Start conversation with timeout
            result = await asyncio.wait_for(
                user_proxy.a_initiate_chat(
                    group_chat_manager,
                    message=initial_message,
                    max_turns=6
                ),
                timeout=300  # 5 minutes max
            )

            logger.info("SUCCESS: Conversation completed normally")
                
        except asyncio.TimeoutError:
            logger.error("TIMEOUT: Conversation exceeded 3 minutes")
        except Exception as e:
            logger.error(f"CONVERSATION ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
        # Display conversation results
        if group_chat.messages:
            logger.info("")
            logger.info("="*60)
            logger.info("CONVERSATION FLOW RESULTS")
            logger.info("="*60)
            
            for i, msg in enumerate(group_chat.messages, 1):
                speaker = msg.get('name', 'Unknown')
                content = msg.get('content', '')
                
                # Show full content for important messages, truncated for others
                if speaker in ['DecisionOrchestrator'] or 'Upload Instructions:' in content:
                    display_content = content
                else:
                    display_content = content[:200] + "..." if len(content) > 200 else content
                
                logger.info(f"{i}. {speaker}:")
                logger.info(f"   {display_content}")
                logger.info("")
            
            logger.info("="*60)
            logger.info("CONVERSATION COMPLETED")
            logger.info("="*60)
        else:
            logger.warning("No messages found in conversation!")

    except Exception as e:
        logger.error(f"MAIN ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())