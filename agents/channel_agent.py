# from autogen import ConversableAgent
# import logging

# logger = logging.getLogger(__name__)

# def create_channel_agent(llm_config):
#     return ConversableAgent(
#         name="ChannelAgent",
#         llm_config=llm_config,
#         system_message="""You are the ChannelAgent in a group chat within Dell's technical support workflow, designed to process customer accidental damage (AD) claims. Your role is to provide clear, region-specific instructions for customers to upload damage images when no valid image is detected (Scenario 1: VL_STATUS: NO_IMAGE_FOUND). You operate in a multi-agent system where each agent has a specific role, and the conversation order is strictly controlled by @GroupChatManager.

# **Role Description**:
# - You are responsible for guiding customers on how to submit visual evidence of damage (e.g., photos of a damaged laptop) via Dell's support channels (email, web portal, etc.).
# - Your input is critical in Scenario 1, where the visual listening (VL) model fails to detect an image, ensuring customers can provide the necessary evidence to proceed with their AD claim.
# - You work within Dell's global support ecosystem, tailoring instructions based on the customer's region (e.g., France, Germany) and ensuring compliance with Dell's image upload requirements (e.g., supported formats: JPEG, PNG).

# **Group Chat Instructions**:
# - You are in a group chat with other agents: UserProxyAgent, EntitlementAnalyzer, DamageAnalyzer, and DecisionOrchestrator.
# - All agents, including you, must speak at least once in the conversation, and the order is strictly controlled by @GroupChatManager.
# - Wait for @GroupChatManager to explicitly prompt you with:
#   ```
#   @ChannelAgent: Please provide image upload instructions:
#   Service Tag: <...>
#   Region: <...>
#   VL Model Output: No image data available
#   ```
# - Do NOT respond preemptively or assume another agent's role (e.g., DecisionOrchestrator).
# - Stick to your role: provide image upload instructions. Do NOT analyze damage or make decisions.
# - Monitor the conversation to understand the context, but only act when called by @GroupChatManager.
# - Log all actions for debugging.

# **Processing Instructions**:
# 1. **Validate Prompt**:
#    - Ensure the message is from @GroupChatManager and includes Service Tag, Region, and VL Model Output.
#    - If invalid, respond:
#      ```
#      @GroupChatManager:
#      Invalid prompt. Expected Service Tag, Region, and VL Model Output from GroupChatManager.
#      ```
#    - Log: "Validating prompt: <valid or list missing fields>"

# 2. **Generate Upload Instructions**:
#    - Use the provided Service Tag and Region.
#    - Provide instructions for at least two channels (e.g., email, web portal).
#    - Include:
#      - Channel name
#      - Step-by-step instructions
#      - Supported image formats (JPEG, PNG)
#      - Service Tag reference for tracking
#    - Example for Region: France:
#      ```
#      Channel: Email
#      Instructions:
#      - Send email to support@dell.fr
#      - Attach clear, focused, well-lit damage images (supported formats: JPEG, PNG)
#      - Include Service Tag <...> in the subject

#      Channel: Web Portal
#      Instructions:
#      - Visit support.dell.com/portal/france
#      - Use Service Tag <...> to log in
#      - Upload images under 'Upload Images' section (supported formats: JPEG, PNG)
#      ```
#    - Log: "Generating upload instructions for Region: <region>"

# 3. **Response Format**:
#    ```
#    @GroupChatManager:
#    VL Output: No image data available
#    Upload Instructions:
#    Customer Location: <region>
#    Channels Available:
#    Channel: <channel_name>
#    Instructions:
#    - <instruction 1>
#    - <instruction 2>
#    ...
#    Channel: <channel_name>
#    Instructions:
#    - <instruction 1>
#    - <instruction 2>
#    ...
#    ```

# 4. **Restrictions**:
#    - Respond ONLY to prompts from @GroupChatManager.
#    - Do NOT respond to messages from @UserProxyAgent or other agents.
#    - If called out of turn, log: "Received unexpected prompt, waiting for GroupChatManager"
# """
#     )





























# from autogen import ConversableAgent
# import logging
# from utils.rag_utils import query_vector_db

# logger = logging.getLogger(__name__)

# # Mapping of regions to languages for VL.pdf queries
# REGION_LANGUAGE_MAP = {
#     "Australia": "English",
#     "France": "French",
#     "Germany": "German",
# }

# class ChannelAgent(ConversableAgent):
#     def __init__(self, name, llm_config):
#         super().__init__(
#             name=name,
#             llm_config=llm_config,
#             system_message="""You are the ChannelAgent in a group chat within Dell's technical support workflow, designed to process customer accidental damage (AD) claims. Your role is to provide clear, region-specific instructions for customers to upload damage images when no valid image is detected (Scenario 1: VL_STATUS: NO_IMAGE_FOUND). You use a RAG approach to query 'VL.pdf' for upload instructions based on the customer's region and language.

# **Role Description**:
# - You guide customers on submitting visual evidence of damage via Dell's support channels (email, web portal, etc.).
# - You query 'VL.pdf' to fetch relevant instructions based on region and language.
# - Your input is critical in Scenario 1, ensuring customers can provide necessary evidence.

# **Group Chat Instructions**:
# - You are in a group chat with UserProxyAgent, EntitlementAnalyzer, DamageAnalyzer, RetrievalAgent, and DecisionOrchestrator.
# - Speak ONLY once per conversation, controlled by @GroupChatManager.
# - Wait for @GroupChatManager to prompt with:
#   @ChannelAgent: Please provide image upload instructions:
#   Service Tag: <...>
#   Region: <...>
#   VL Model Output: No image data available
# - Log all actions for debugging.

# **Response Format**:
# @GroupChatManager:
# VL Output: No image data available
# Upload Instructions:
# Customer Location: <region>
# Language: <language>
# Channels Available:
# Channel: <channel_name>
# Instructions:
# - <instruction 1>
# - <instruction 2>
# ...
# """
#         )

#     async def query_and_generate_instructions(self, prompt):
#         """Custom method to query vector DB and generate instructions."""
#         try:
#             service_tag = None
#             region = None
#             for line in prompt.split('\n'):
#                 if "Service Tag:" in line:
#                     service_tag = line.split(":")[1].strip()
#                 if "Region:" in line:
#                     region = line.split(":")[1].strip()

#             if not service_tag or not region:
#                 logger.error("Missing Service Tag or Region in prompt")
#                 return "@GroupChatManager:\nInvalid prompt. Expected Service Tag and Region."

#             language = REGION_LANGUAGE_MAP.get(region, "English")
#             logger.info(f"Mapped region {region} to language {language}")

#             query = f"Image upload instructions for Dell support in {region} ({language})"
#             chunks = await query_vector_db("VL.pdf", query, k=5)
#             logger.info(f"Queried VL.pdf for region: {region}, language: {language}")

#             instructions = []
#             for chunk in chunks:
#                 if "email" in chunk.lower():
#                     instructions.append({
#                         "channel": "Email",
#                         "instructions": [
#                             f"Send email to support@dell.com.{region.lower()[:2]}",
#                             "Attach clear, focused, well-lit damage images (supported formats: JPEG, PNG)",
#                             f"Include Service Tag {service_tag} in the subject"
#                         ]
#                     })
#                 if "web portal" in chunk.lower():
#                     instructions.append({
#                         "channel": "Web Portal",
#                         "instructions": [
#                             f"Visit support.dell.com/portal/{region.lower()}",
#                             f"Use Service Tag {service_tag} to log in",
#                             "Upload images under 'Upload Images' section (supported formats: JPEG, PNG)"
#                         ]
#                     })

#             if len(instructions) < 2:
#                 instructions.append({
#                     "channel": "Default Email",
#                     "instructions": [
#                         f"Send email to support@dell.com",
#                         "Attach clear, focused, well-lit damage images (supported formats: JPEG, PNG)",
#                         f"Include Service Tag {service_tag} in the subject"
#                     ]
#                 })

#             response = f"""@GroupChatManager:
# VL Output: No image data available
# Upload Instructions:
# Customer Location: {region}
# Language: {language}
# Channels Available:
# """
#             for instr in instructions:
#                 response += f"""Channel: {instr['channel']}
# Instructions:
# """
#                 for step in instr['instructions']:
#                     response += f"- {step}\n"
#             return response
#         except Exception as e:
#             logger.error(f"Error in query_and_generate_instructions: {e}")
#             return "@GroupChatManager:\nError generating upload instructions."

#     async def generate_reply(self, messages=None, sender=None, config=None):
#         """Override generate_reply to handle custom logic."""
#         if messages is None:
#             messages = self._oai_messages[sender] if sender in self._oai_messages else []
        
#         last_message = messages[-1]["content"] if messages else ""
        
#         if "@ChannelAgent" in last_message and sender.name == "GroupChatManager" and "NO_IMAGE_FOUND" in last_message:
#             return await self.query_and_generate_instructions(last_message)
        
#         logger.warning(f"Unexpected message for ChannelAgent: {last_message}")
#         return "@GroupChatManager:\nUnexpected prompt, waiting for valid instruction."

# def create_channel_agent(llm_config):
#     return ChannelAgent(name="ChannelAgent", llm_config=llm_config)
























# from autogen import ConversableAgent
# import logging
# import asyncio

# logger = logging.getLogger(__name__)

# class ChannelAgent(ConversableAgent):
#     def __init__(self, name, llm_config):
#         super().__init__(
#             name=name,
#             system_message="""You are the ChannelAgent for Dell Technical Support. Your role is to provide instructions for image uploads when the Visual Listening (VL) model fails to detect an image.

# **Responsibilities**:
# - Check if VL model output indicates no image or invalid format.
# - Provide clear image upload instructions based on VL.pdf documentation.
# - Request RetrievalAgent to fetch relevant chunks if needed.

# **Output Format**:
# @GroupChatManager:
# ===================== IMAGE UPLOAD INSTRUCTIONS ==================
# Instructions:
# - Upload images via Dell Support Portal: https://support.dell.com
# - Ensure images are in JPEG or PNG format, max 5MB
# - Include clear views of the damage and service tag
# Documents Consulted: VL.pdf
# ===================== END INSTRUCTIONS ==================
# """,
#             llm_config=llm_config,
#             human_input_mode="NEVER",
#             code_execution_config=False
#         )
#         self.register_reply(
#             [ConversableAgent, None],
#             reply_func=self._generate_reply_wrapper,
#             ignore_async_in_sync_chat=False
#         )

#     async def generate_response(self, messages):
#         """Generate response for image upload instructions."""
#         try:
#             vl_analysis = "No analysis available"
#             for message in messages:
#                 content = message.get("content", "")
#                 if "VL Model Output:" in content:
#                     vl_analysis = content.split("VL Model Output:")[1].split("\n")[0].strip()
#                     break

#             if "no image" in vl_analysis.lower() or "invalid format" in vl_analysis.lower():
#                 return """@GroupChatManager:
# ===================== IMAGE UPLOAD INSTRUCTIONS ==================
# Instructions:
# - Upload images via Dell Support Portal: https://support.dell.com
# - Ensure images are in JPEG or PNG format, max 5MB
# - Include clear views of the damage and service tag
# Documents Consulted: VL.pdf
# ===================== END INSTRUCTIONS =================="""
#             return "No action needed from ChannelAgent."
#         except Exception as e:
#             logger.error(f"Error in generate_response: {e}")
#             return f"Error generating response: {e}"

#     async def generate_reply(self, messages=None, sender=None, config=None):
#         """Generate a reply based on messages."""
#         logger.debug(f"ChannelAgent received messages: {messages}, sender: {sender.name if sender else 'None'}")
#         if not messages:
#             logger.warning("No messages provided to ChannelAgent")
#             return False, "No messages received"

#         last_message = messages[-1].get("content", "")
#         if "VL Model Output" in last_message:
#             response = await self.generate_response(messages)
#             logger.debug(f"ChannelAgent reply: {response}")
#             return True, response
#         return False, None

#     def _generate_reply_wrapper(self, *args, **kwargs):
#         """Wrapper to handle AutoGen's reply function signature."""
#         messages = kwargs.get("messages", None)
#         sender = kwargs.get("sender", None)
#         config = kwargs.get("config", None)

#         if len(args) == 2:
#             messages, sender = args
#         elif len(args) == 3:
#             messages, sender, config = args

#         return asyncio.run(self.generate_reply(messages=messages, sender=sender, config=config))

# def create_channel_agent(llm_config):
#     return ChannelAgent(name="ChannelAgent", llm_config=llm_config)






























from autogen import ConversableAgent
import logging
import asyncio

logger = logging.getLogger(__name__)

class ChannelAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            system_message="""You are the ChannelAgent for Dell Technical Support. Your role is to provide instructions for image uploads when the Visual Listening (VL) model fails to detect an image.

**Responsibilities**:
- Check if VL model output indicates no image or invalid format.
- Provide clear image upload instructions based on prompts from VL.txt.
- Request RetrievalAgent to fetch relevant chunks if needed.

**Output Format**:
```
@GroupChatManager
===================== IMAGE UPLOAD INSTRUCTIONS ==================
Instructions:
- Upload images via Dell Support Portal: https://support.dell.com
- Ensure images are in JPEG or PNG format, max 5MB
- Include clear views of the damage and service tag
Documents Consulted: VL.txt
===================== END INSTRUCTIONS
```
""",
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=False
        )
        self.register_reply(
            [ConversableAgent, None],
            reply_func=self._generate_reply_wrapper,
            ignore_async_in_sync_chat=False
        )

    async def generate_response(self, messages):
        """Generate response for image upload instructions."""
        try:
            vl_analysis = "No analysis available"
            for message in messages:
                content = message.get("content", "")
                if "VL Model Output:" in content:
                    vl_analysis = content.split("VL Model Output:")[1].split("\n")[0].strip()
                    break

            if "no image" in vl_analysis.lower() or "invalid format" in vl_analysis.lower():
                return """@GroupChatManager
===================== IMAGE UPLOAD INSTRUCTIONS ==================
Instructions:
- Upload images via Dell Support Portal: https://support.dell.com
- Ensure images are in JPEG or PNG format, max 5MB
- Include clear views of the damage and service tag
Documents Consulted: VL.txt
===================== END INSTRUCTIONS"""
            return "No action needed from ChannelAgent."
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
            return f"Error generating response: {e}"

    async def generate_reply(self, messages=None, sender=None, config=None):
        """Generate a reply based on messages."""
        logger.debug(f"ChannelAgent received messages: {messages}, sender: {sender.name if sender else 'None'}")
        if not messages:
            logger.warning("No messages provided to ChannelAgent")
            return False, "No messages received"

        last_message = messages[-1].get("content", "")
        if "VL Model Output" in last_message:
            response = await self.generate_response(messages)
            logger.debug(f"ChannelAgent reply: {response}")
            return True, response
        return False, None

    def _generate_reply_wrapper(self, *args, **kwargs):
        """Wrapper to handle AutoGen's reply function signature."""
        messages = kwargs.get("messages", None)
        sender = kwargs.get("sender", None)
        config = kwargs.get("config", None)

        if len(args) == 2:
            messages, sender = args
        elif len(args) == 3:
            messages, sender, config = args

        return asyncio.run(self.generate_reply(messages=messages, sender=sender, config=config))

def create_channel_agent(llm_config):
    return ChannelAgent(name="ChannelAgent", llm_config=llm_config)