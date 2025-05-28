from autogen import ConversableAgent
import logging
import re

logger = logging.getLogger(__name__)

def create_channel_agent(llm_config, agent_name="ChannelAgent"):
    def determine_language(region, llm_config):
        try:
            language_detector = ConversableAgent(
                name="LanguageDetector",
                llm_config=llm_config,
                system_message="Return only the primary language for the given region (e.g., 'French' for France).",
                human_input_mode="NEVER",
                code_execution_config=False
            )
            prompt = f"What is the primary language for {region}?"
            response = language_detector.generate_reply(messages=[{"content": prompt, "role": "user"}])
            logger.info(f"LanguageDetector response for {region}: {response}")
            return response.strip() if response else "English"
        except Exception as e:
            logger.error(f"Error determining language for {region}: {e}")
            return "English"

    def extract_channels_and_details(chunks):
        channels = []
        for chunk in chunks:
            channel_matches = re.findall(r'\b(WhatsApp|Email|WeChat|Line|Apple Business Chat|Google Business Messenger)\b', chunk, re.IGNORECASE)
            for channel in set(channel_matches):
                channel = channel.lower()
                details = {}
                phone_matches = re.findall(r'\+[\d\s()-]{8,20}', chunk)
                if phone_matches and channel in ["whatsapp", "line", "wechat"]:
                    details["phone"] = phone_matches[0].strip()
                email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', chunk)
                if email_matches and channel == "email":
                    details["email"] = email_matches[0].strip()
                lines = chunk.split('\n')
                instructions = []
                for i, line in enumerate(lines):
                    if channel in line.lower() and i + 1 < len(lines):
                        instructions.extend([l.strip() for l in lines[i+1:i+4] if l.strip()])
                if details or instructions:
                    channels.append({
                        "name": channel.capitalize(),
                        "details": details,
                        "instructions": instructions[:2]
                    })
        return channels

    return ConversableAgent(
        name=agent_name,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="""You are the ChannelAgent in Dell's technical support workflow for accidental damage claims. Your role is to provide region-specific image upload instructions in ENGLISH ONLY for Scenario 1 (NO_IMAGE_FOUND), using chunks from 'VL.pdf' fetched by RetrievalAgent via cosine similarity search.

**Processing Instructions**:
1. Wait for @GroupChatManager prompt:
   ```
   @ChannelAgent: Please provide image upload instructions:
   Service Tag: <service_tag>
   Region: <region>
   VL Model Output: <vl_model_output>
   ```
   - Validate: Ensure Service Tag, Region, VL Model Output, and @GroupChatManager format.
   - If invalid, respond: "@GroupChatManager: Invalid prompt: missing fields [list] or wrong format."
   - Log: "Validating prompt: <valid or missing fields>"
2. Determine language for querying.
   - Log: "Determined language <language> for region <region>"
3. Request chunks:
   - Respond: "@ChannelAgent_RetrievalAgent: Fetch chunks for VL.pdf with query: Image upload instructions for Dell support in location <region> language <language>"
4. Wait for RetrievalAgent:
   - Format: "@ChannelAgent: Retrieved chunks:\n<chunk1>\n<chunk2>\n..."
   - If no chunks, respond: "@GroupChatManager: Error: No upload instructions found for <region>."
5. Process chunks:
   - Summarize each in English (1-2 sentences).
   - Extract channels (e.g., WhatsApp, Email) and details (phone numbers, emails) dynamically.
   - Validate: Ensure at least one channel with contact details.
   - If invalid, respond: "@GroupChatManager: No valid channels or contact details found."
6. Generate ENGLISH instructions:
   - Include: channel, method, steps, JPEG/PNG formats, Service Tag reference.
7. Response Format:
   ```
   @GroupChatManager:
   VL Output: No image data available
   Upload Instructions:
   Customer Location: <region>
   Language: <language> (used for query)
   Channels:
   - Channel: <channel>
     Instructions:
     - <step 1, e.g., contact via phone/email>
     - Send JPEG/PNG images, include Service Tag <service_tag>.
   Chunk Summaries:
   - Chunk 1: <summary in English>
   - ...
   Full Chunks:
   - Chunk 1: <full content>
   - ...
   Documents Consulted: VL.pdf
   ```
8. Restrictions:
   - ENGLISH ONLY output.
   - Respond only to @GroupChatManager or @ChannelAgent_RetrievalAgent.
   - Log: "Unexpected prompt from <agent_name>"
9. Errors: "@GroupChatManager: Error generating instructions: <error>."
"""
    )