from autogen import ConversableAgent
import logging
import re
import asyncio
from utils.rag_utils import query_vector_db

logger = logging.getLogger(__name__)

# Agent to table mapping
AGENT_TABLE_MAP = {
    "ChannelAgent": {
        "table": "channel_agent",
        "pdfs": ["VL.pdf"]
    },
    "EntitlementAnalyzer": {
        "table": "entitlement_analyzer", 
        "pdfs": ["AccidentalDamage.pdf", "DELLSW.pdf"]
    },
    "DamageAnalyzer": {
        "table": "damage_analyzer",
        "pdfs": ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]
    }
}

class RetrievalAgent(ConversableAgent):
    def __init__(self, agent_name, llm_config):
        self.agent_name = agent_name
        self.table_info = AGENT_TABLE_MAP.get(agent_name)
        
        if not self.table_info:
            raise ValueError(f"No table mapping found for agent: {agent_name}")
        
        self.table_name = self.table_info["table"]
        self.pdf_list = self.table_info["pdfs"]
        retrieval_agent_name = f"{agent_name}_RetrievalAgent"
        
        # Simple system message for retrieval agents
        system_message = f"""You are {retrieval_agent_name}. 
When you receive a query, search the database and return the results.
Always respond with the chunks you find."""
        
        super().__init__(
            name=retrieval_agent_name,
            system_message=system_message,
            llm_config=None,  # No LLM needed for retrieval
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=1,
            is_termination_msg=lambda x: False
        )
        
        logger.info(f"Created {retrieval_agent_name} for table '{self.table_name}' with PDFs: {self.pdf_list}")
    
    def _run_async_query(self, query_text, region=None, language=None):
        """Run async query with proper timeout handling"""
        all_results = []
        
        try:
            # Handle async context properly
            try:
                loop = asyncio.get_running_loop()
                # We're already in an async context
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    async def query_all_pdfs():
                        results = []
                        for pdf_name in self.pdf_list:
                            logger.info(f"🔍 Querying {pdf_name} for {self.agent_name}...")
                            
                            try:
                                pdf_results = await asyncio.wait_for(
                                    query_vector_db(
                                        pdf_name=pdf_name,
                                        query=query_text,
                                        k=5,  # Get top 5 chunks as requested
                                        region=region,
                                        language=language,
                                        table_name=self.table_name
                                    ),
                                    timeout=10
                                )
                                
                                if pdf_results and pdf_results.get('chunks'):
                                    for i, chunk in enumerate(pdf_results['chunks']):
                                        results.append({
                                            'text': chunk,
                                            'source': pdf_name,
                                            'similarity': pdf_results.get('similarities', [0])[i] if pdf_results.get('similarities') else 0
                                        })
                                        
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout querying {pdf_name}")
                                continue
                            except Exception as e:
                                logger.error(f"Error querying {pdf_name}: {e}")
                                continue
                        
                        return results
                    
                    try:
                        return new_loop.run_until_complete(query_all_pdfs())
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    all_results = future.result(timeout=25)
                    
            except RuntimeError:
                # No running loop, use asyncio.run
                async def query_all_pdfs():
                    results = []
                    for pdf_name in self.pdf_list:
                        logger.info(f"🔍 Querying {pdf_name} for {self.agent_name}...")
                        
                        try:
                            pdf_results = await asyncio.wait_for(
                                query_vector_db(
                                    pdf_name=pdf_name,
                                    query=query_text,
                                    k=5,  # Get top 5 chunks as requested
                                    region=region,
                                    language=language,
                                    table_name=self.table_name
                                ),
                                timeout=10
                            )
                            
                            if pdf_results and pdf_results.get('chunks'):
                                for i, chunk in enumerate(pdf_results['chunks']):
                                    results.append({
                                        'text': chunk,
                                        'source': pdf_name,
                                        'similarity': pdf_results.get('similarities', [0])[i] if pdf_results.get('similarities') else 0
                                    })
                                    
                        except asyncio.TimeoutError:
                            logger.warning(f"Timeout querying {pdf_name}")
                            continue
                        except Exception as e:
                            logger.error(f"Error querying {pdf_name}: {e}")
                            continue
                    
                    return results
                
                all_results = asyncio.run(query_all_pdfs())
            
            # Sort by similarity and take top 5
            if all_results:
                all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                return all_results[:5]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in async query for {self.agent_name}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_reply(self, messages=None, sender=None, **kwargs):
        """FIXED: Enhanced retrieval with better message handling"""
        try:
            # Debug logging
            logger.info(f"RetrievalAgent {self.name} called")
            logger.info(f"Messages type: {type(messages)}")
            logger.info(f"Sender: {sender.name if hasattr(sender, 'name') else sender}")
            
            # FIX 1: Handle None messages by getting from sender's chat history
            if not messages and hasattr(sender, 'chat_messages'):
                # Get messages from the sender's chat history
                for participant, msg_list in sender.chat_messages.items():
                    if msg_list:
                        messages = msg_list
                        logger.info(f"Retrieved messages from sender's chat history with {participant}")
                        break
            
            if not messages:
                logger.error("No messages provided to retrieval agent")
                return "Retrieved chunks:\n\nNo relevant policy data found - no messages received."
            
            # Handle different message formats
            if isinstance(messages, list):
                message_list = messages
            elif isinstance(messages, dict):
                message_list = [messages]
            else:
                logger.error(f"Unexpected messages type: {type(messages)}")
                return "Retrieved chunks:\n\nError: Invalid message format"
            
            # FIX 2: Look for messages directed to this agent in the recent conversation
            message_content = ""
            found_request = False
            
            # Search through ALL messages for our agent request
            for msg in reversed(message_list):
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                else:
                    content = str(msg)
                
                # Check if this message contains a request for us
                if f"@{self.name}:" in content:
                    message_content = content
                    found_request = True
                    logger.info(f"Found request for {self.name}")
                    break
            
            if not found_request:
                logger.warning(f"No request found for {self.name} in messages")
                # FIX 3: Also check the last few messages for any requests
                recent_content = ""
                for msg in message_list[-3:]:
                    if isinstance(msg, dict):
                        recent_content += msg.get("content", "") + " "
                    else:
                        recent_content += str(msg) + " "
                
                if f"@{self.name.replace('_RetrievalAgent', '')}_RetrievalAgent:" in recent_content:
                    message_content = recent_content
                    found_request = True
                    logger.info(f"Found request in combined recent messages")
                
                if not found_request:
                    return "Retrieved chunks:\n\nNo relevant policy data found - no request detected."
            
            logger.info(f"Processing request: {message_content[:100]}...")
            
            # Extract query from message
            try:
                # Clean the query - look for the pattern after our agent name
                query_pattern = rf"@{self.name}:\s*(.+?)(?=@|\n\n|$)"
                query_match = re.search(query_pattern, message_content, re.DOTALL)
                
                if not query_match:
                    # Try alternative patterns
                    alt_pattern = rf"@{self.name.replace('_RetrievalAgent', '')}_RetrievalAgent:\s*(.+?)(?=@|\n\n|$)"
                    query_match = re.search(alt_pattern, message_content, re.DOTALL)
                
                if not query_match:
                    logger.error(f"Could not extract query from message")
                    return "Retrieved chunks:\n\nNo relevant policy data found - could not parse query."
                
                query_text = query_match.group(1).strip()
                
                # Clean up query text - remove brackets and formatting
                query_text = re.sub(r'\[([^\]]+)\]', r'\1', query_text)  # Remove brackets
                query_text = re.sub(r'\*\*.*?\*\*', '', query_text)  # Remove markdown
                query_text = re.sub(r'```.*?```', '', query_text, flags=re.DOTALL)  # Remove code blocks
                query_text = ' '.join(query_text.split())  # Normalize whitespace
                
                logger.info(f"Cleaned query: {query_text}")
                
                if not query_text:
                    logger.error("Empty query after parsing")
                    return "Retrieved chunks:\n\nNo relevant policy data found - empty query."
                
                # Extract region and language if present
                region_match = re.search(r"region\s+(\w+)", query_text, re.IGNORECASE)
                language_match = re.search(r"language\s+(\w+)", query_text, re.IGNORECASE)
                
                region = region_match.group(1) if region_match else None
                language = language_match.group(1) if language_match else None
                
                if region:
                    logger.info(f"Extracted region: {region}")
                if language:
                    logger.info(f"Extracted language: {language}")
                
                # Run the database query
                logger.info(f"Starting database query for {self.agent_name}...")
                top_results = self._run_async_query(query_text, region, language)
                
                logger.info(f"Retrieved {len(top_results)} chunks from vector database")
                
                # Format response with exactly top 5 chunks
                if not top_results:
                    return f"Retrieved chunks:\n\nNo relevant policy data found in {', '.join(self.pdf_list)} for query: {query_text[:50]}..."
                
                # Build response with exactly 5 chunks (or less if not available)
                response_lines = ["Retrieved chunks:", ""]
                
                for i, result in enumerate(top_results[:5], 1):  # Ensure max 5 chunks
                    # Truncate very long chunks
                    chunk_text = result['text']
                    if len(chunk_text) > 800:
                        chunk_text = chunk_text[:800] + "..."
                    
                    response_lines.append(f"**Chunk {i}** (from {result['source']}, similarity: {result.get('similarity', 0):.3f}):")
                    response_lines.append(chunk_text)
                    response_lines.append("")
                
                response_lines.append(f"**Total chunks retrieved: {len(top_results)} from {', '.join(self.pdf_list)}**")
                
                response = "\n".join(response_lines)
                logger.info(f"Returning {len(top_results)} chunks to {self.agent_name}")
                
                return response
                
            except Exception as e:
                error_msg = f"Retrieved chunks:\n\nError processing query: {str(e)}"
                logger.error(f"Error processing query: {e}")
                import traceback
                traceback.print_exc()
                return error_msg
                
        except Exception as e:
            error_msg = f"Retrieved chunks:\n\nRetrieval agent error: {str(e)}"
            logger.error(f"Error in retrieval agent: {e}")
            import traceback
            traceback.print_exc()
            return error_msg


# Factory functions to create specific retrieval agents
def create_entitlement_retrieval_agent():
    """Create retrieval agent for EntitlementAnalyzer"""
    return RetrievalAgent("EntitlementAnalyzer", llm_config=None)


def create_channel_retrieval_agent():
    """Create retrieval agent for ChannelAgent"""
    return RetrievalAgent("ChannelAgent", llm_config=None)


def create_damage_retrieval_agent():
    """Create retrieval agent for DamageAnalyzer"""
    return RetrievalAgent("DamageAnalyzer", llm_config=None)