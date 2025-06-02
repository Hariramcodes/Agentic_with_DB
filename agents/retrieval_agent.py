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

            # Validate the request format
            pattern = r"@ChannelAgent_RetrievalAgent: Fetch chunks for VL\.pdf with query: (.+?)(?:\n|$)"
            match = re.search(pattern, last_message, re.DOTALL)
            
            if not match:
                logger.error(f"Invalid prompt format: {last_message[:200]}...")
                return (False, "@ChannelAgent: Invalid request format. Expected @ChannelAgent_RetrievalAgent format.")

            query = match.group(1).strip()
            logger.info(f"Parsed query: {query}")

            # Extract region and language from query
            region_match = re.search(r"location (\w+)", query)
            language_match = re.search(r"language (\w+)", query)
            
            region = region_match.group(1) if region_match else "Unknown"
            language = language_match.group(1) if language_match else "English"
            
            logger.info(f"Extracted region: {region}, language: {language}")

            # Create async function to handle the query
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
                    # If we're already in an async context, we need to handle this differently
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
                logger.warning("No chunks retrieved from database")
                return (False, "@ChannelAgent: Error retrieving chunks: No results found for the specified query.")

            # Format the response with retrieved chunks
            response = "@ChannelAgent: Retrieved chunks:\n" + "\n---CHUNK_SEPARATOR---\n".join(chunks)
            logger.info(f"Sending response with {len(chunks)} chunks to ChannelAgent")
            
            return (False, response)

        except Exception as e:
            logger.error(f"Error in RetrievalAgent process_message: {str(e)}")
            return (False, f"@ChannelAgent: Error retrieving chunks: {str(e)}")

    # Create the agent
    agent = ConversableAgent(
        name=f"{agent_name}_RetrievalAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message=f"""You are the {agent_name}_RetrievalAgent responsible for fetching relevant chunks from the vector database. 

**Processing Instructions**:
1. Wait for requests in the format: "@ChannelAgent_RetrievalAgent: Fetch chunks for VL.pdf with query: <query>"
2. Extract the query, region, and language from the request
3. Query the vector database for exactly 5 chunks from VL.pdf
4. Return the chunks to the requesting agent in the format: "@ChannelAgent: Retrieved chunks:" followed by the chunks

**Important Guidelines**:
- Only respond to properly formatted requests
- Always fetch exactly 5 chunks when available
- Include region and language context in the search
- Handle errors gracefully and inform the requesting agent
"""
    )

    # Register the custom reply function
    agent.register_reply(
        trigger=ConversableAgent,
        reply_func=process_message
    )

    return agent