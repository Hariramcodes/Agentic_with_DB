import asyncio
import logging
from autogen import ConversableAgent
from agents.retrieval_agent import create_retrieval_agent
from config.llm_config import llm_config

logger = logging.getLogger(__name__)

async def test_retrieval_agent():
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger.info("Starting RetrievalAgent test")

        # Create RetrievalAgent
        retrieval_agent = create_retrieval_agent(llm_config, "ChannelAgent")

        # Simulate a test message
        test_message = {
            "content": "@ChannelAgent_RetrievalAgent: Fetch chunks for VL.pdf with query: Image upload instructions for Dell support in location France language French",
            "name": "TestSender"
        }

        # Create a dummy sender agent
        dummy_sender = ConversableAgent(
            name="TestSender",
            llm_config=False,
            human_input_mode="NEVER",
            code_execution_config=False
        )

        # Simulate message processing
        logger.info("Sending test message to RetrievalAgent")
        result = await retrieval_agent.a_generate_reply(
            messages=[test_message],
            sender=dummy_sender,
            config=None
        )

        if result and isinstance(result, tuple) and result[0]:
            logger.info(f"RetrievalAgent response:\n{result[1]}")
        elif result and isinstance(result, str):
            logger.info(f"RetrievalAgent response:\n{result}")
        else:
            logger.error("RetrievalAgent returned no response or invalid response format")

    except Exception as e:
        logger.error(f"Error in test_retrieval_agent: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_retrieval_agent())
