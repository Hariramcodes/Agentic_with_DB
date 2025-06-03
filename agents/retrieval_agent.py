from autogen import ConversableAgent
import logging
import re
import asyncio
from utils.rag_utils import query_vector_db

logger = logging.getLogger(__name__)

def create_retrieval_agent(llm_config, agent_name):
    def process_message(recipient, messages, sender, config):
        try:
            last_message = messages[-1]["content"]
            logger.info(f"RetrievalAgent received message: {last_message[:100]}...")

            # Validate and extract prompt
            pattern = r"@ChannelAgent_RetrievalAgent: Fetch chunks for VL\.pdf with query: (.+?)(?:\n|$)"
            match = re.search(pattern, last_message, re.DOTALL)
            if not match:
                logger.error(f"Invalid prompt format: {last_message[:200]}...")
                return (False, "@ChannelAgent: Invalid caller or format.")

            query = match.group(1).strip()
            logger.info(f"Parsed query: {query}")

            # Extract region and language
            region_match = re.search(r"location (\w+)", query)
            language_match = re.search(r"language (\w+)", query)
            region = region_match.group(1) if region_match else "Unknown"
            language = language_match.group(1) if language_match else "English"
            logger.info(f"Extracted region: {region}, language: {language}")

            # Query vector DB
            async def async_query():
                try:
                    result = await query_vector_db(
                        pdf_name="VL.pdf",
                        query=query,
                        k=5,
                        region=region,
                        language=language
                    )
                    return result
                except Exception as e:
                    logger.error(f"Error in async_query: {str(e)}")
                    return {"chunks": [], "ids": []}

            # Run the async query
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, async_query())
                        result = future.result(timeout=30)
                else:
                    result = loop.run_until_complete(async_query())
            except Exception as e:
                logger.error(f"Error running async query: {str(e)}")
                return (False, f"@ChannelAgent: Error retrieving chunks: {str(e)}")

            chunks = result.get("chunks", [])
            logger.info(f"Retrieved {len(chunks)} chunks from vector database")

            if not chunks:
                logger.warning("No chunks retrieved")
                return (False, "@ChannelAgent: Error retrieving chunks: No results found.")

            # Format response with the exact chunks retrieved from database
            response = "@ChannelAgent: Retrieved chunks:\n" + "\n---CHUNK_SEPARATOR---\n".join(chunks)
            logger.info(f"Sending response structure: type={type(response)}, content={response[:100]}...")
            return (False, response)
            
        except Exception as e:
            logger.error(f"Error in RetrievalAgent: {str(e)}")
            return (False, f"@ChannelAgent: Error retrieving chunks: {str(e)}")

    agent = ConversableAgent(
        name=f"{agent_name}_RetrievalAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="You are a RetrievalAgent that fetches chunks from a vector database for ChannelAgent using a defined function. You do not generate responses - only use the function."
    )

    # Register custom reply function
    agent.register_reply(
        trigger=ConversableAgent,
        reply_func=process_message
    )

    return agent