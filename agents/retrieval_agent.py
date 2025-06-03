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
                return (True, "@ChannelAgent: Invalid caller or format.")

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
                return (True, f"@ChannelAgent: Error retrieving chunks: {str(e)}")

            chunks = result.get("chunks", [])
            logger.info(f"Retrieved {len(chunks)} chunks from vector database")

            if not chunks:
                logger.warning("No chunks retrieved")
                return (True, "@ChannelAgent: Error retrieving chunks: No results found.")

            # Build the response with EXACT chunks from database
            response = "@ChannelAgent: Retrieved chunks:\n\n"
            
            for i, chunk in enumerate(chunks, 1):
                response += f"CHUNK {i}:\n{chunk}\n\n---CHUNK_SEPARATOR---\n\n"
            
            # Log the actual chunks being returned
            logger.info(f"Returning {len(chunks)} exact raw chunks to ChannelAgent")
            logger.info(f"Full response being sent: {response[:200]}...")
            
            # Return True to terminate the conversation chain and send this response directly
            return (True, response)
            
        except Exception as e:
            logger.error(f"Error in RetrievalAgent: {str(e)}")
            return (True, f"@ChannelAgent: Error retrieving chunks: {str(e)}")

    # Create agent with minimal LLM config
    agent = ConversableAgent(
        name=f"{agent_name}_RetrievalAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="You are a RetrievalAgent that returns database chunks."
    )

    # Register custom reply function that TERMINATES the conversation
    # This prevents the LLM from processing the response
    agent.register_reply(
        trigger=ConversableAgent,
        reply_func=process_message,
        position=0  # Highest priority
    )

    return agent