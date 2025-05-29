from autogen import ConversableAgent
import logging
import re
import asyncio
from utils.rag_utils import query_vector_db

logger = logging.getLogger(__name__)

def create_retrieval_agent(llm_config, agent_name):
    async def process_message(recipient, messages, sender, config):
        try:
            last_message = messages[-1]["content"]
            logger.info(f"RetrievalAgent received message: {last_message[:100]}...")

            # Validate and extract prompt
            pattern = r"@ChannelAgent_RetrievalAgent: Fetch chunks for VL\.pdf with query: (.+?)(?:\n|$)"
            match = re.search(pattern, last_message, re.DOTALL)
            if not match:
                logger.error(f"Invalid prompt format: {last_message[:200]}...")
                return "@ChannelAgent: Invalid caller or format."

            query = match.group(1).strip()
            logger.info(f"Parsed query: {query}")

            # Extract region and language
            region_match = re.search(r"location (\w+)", query)
            language_match = re.search(r"language (\w+)", query)
            region = region_match.group(1) if region_match else "Unknown"
            language = language_match.group(1) if language_match else "English"
            logger.info(f"Extracted region: {region}, language: {language}")

            # Query vector DB
            logger.info("Calling query_vector_db...")
            result = await query_vector_db(
                pdf_name="VL.pdf",
                query=query,
                k=5,
                region=region,
                language=language
            )
            chunks = result["chunks"]
            logger.info(f"Retrieved {len(chunks)} chunks from rag_utils.py")

            if not chunks:
                logger.warning("No chunks retrieved")
                return "@ChannelAgent: Error retrieving chunks: No results found."

            # Format response
            response = "@ChannelAgent: Retrieved chunks:\n" + "\n".join(chunks)
            logger.info(f"Sending response structure: type={type(response)}, content={response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Error in RetrievalAgent: {str(e)}")
            return f"@ChannelAgent: Error retrieving chunks: {str(e)}"

    agent = ConversableAgent(
        name=f"{agent_name}_RetrievalAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="You are a RetrievalAgent that fetches chunks from a vector database for ChannelAgent using a defined function."
    )

    # Register custom reply function
    agent.register_reply(
        trigger=ConversableAgent,  # Apply to all ConversableAgent instances
        reply_func=process_message
    )

    return agent