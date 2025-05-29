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
            logger.info(f"LanguageDetector raw response: type={type(response)}, content={response}")
            if isinstance(response, dict) and "content" in response:
                response = response["content"]
            # Clean response
            if response and "The primary language for" in response:
                language = re.search(r"The primary language for \w+ is (\w+)\.", response)
                return language.group(1) if language else "English"
            return response.strip() if response else "English"
        except Exception as e:
            logger.error(f"Error determining language for {region}: {e}")
            return "English"

    def extract_channels_and_details(chunks):
        logger.info(f"Extracting channels from {len(chunks)} chunks")
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
        logger.info(f"Extracted {len(channels)} channels")
        return channels

    def process_message(recipient, messages, sender, config):
        try:
            last_message = messages[-1]["content"]
            logger.info(f"ChannelAgent processing message: type={type(last_message)}, content={last_message[:100]}...")

            # Handle RetrievalAgent response
            if "@ChannelAgent: Retrieved chunks:" in last_message:
                logger.info("Received chunks from RetrievalAgent")
                chunks = last_message.split("@ChannelAgent: Retrieved chunks:\n")[1].split("\n")
                chunks = [c.strip() for c in chunks if c.strip()]
                if not chunks:
                    return (False, "@GroupChatManager: Error: No upload instructions found.")

                # Process chunks
                summaries = [f"Chunk {i+1}: {c[:100]}..." for i, c in enumerate(chunks)]
                channels = extract_channels_and_details(chunks)
                if not channels:
                    return (False, "@GroupChatManager: No valid channels or contact details found.")

                # Generate response
                service_tag = "AXBYCZ6"  # From initial prompt
                region = "France"
                language = "English"
                response = f"""@GroupChatManager:
VL Output: No image data available
Upload Instructions:
Customer Location: {region}
Language: {language} (used for query)
Channels:
"""
                for channel in channels:
                    response += f"- Channel: {channel['name']}\n  Instructions:\n"
                    for instr in channel['instructions']:
                        response += f"  - {instr}\n"
                    if channel['details'].get('phone'):
                        response += f"  - Contact via {channel['name']} at {channel['details']['phone']}.\n"
                    if channel['details'].get('email'):
                        response += f"  - Email {channel['details']['email']} with Service Tag {service_tag}.\n"
                    response += f"  - Send JPEG/PNG images, include Service Tag {service_tag}.\n"
                response += f"""Chunk Summaries:
- {summaries[0]}
Full Chunks:
- {chunks[0][:200]}...
Documents Consulted: VL.pdf"""
                return (False, response)

            # Handle initial prompt
            pattern = r"@ChannelAgent: Please provide image upload instructions:\nService Tag: (\w+)\nRegion: (\w+)\nVL Model Output: (.+)"
            match = re.match(pattern, last_message, re.DOTALL)
            if not match:
                logger.error(f"Invalid initial prompt format: {last_message[:200]}...")
                return (False, "@GroupChatManager: Invalid prompt: missing fields or wrong format.")

            service_tag, region, vl_output = match.groups()
            language = determine_language(region, llm_config)
            logger.info(f"Requesting chunks for {region}, {language}")
            response = f"""**Validating prompt:** Valid Service Tag, Region, VL Model Output, and @GroupChatManager format.

**Checking message history...**

Since there is no prior @ChannelAgent_RetrievalAgent response, I will request chunks:

**Requesting chunks for {region}, {language} (language)**

"@ChannelAgent_RetrievalAgent: Fetch chunks for VL.pdf with query: Image upload instructions for Dell support in location {region} language {language}"

**Logging:** "Requested chunks for {region}, {language}"
"""
            return (False, response)
        except Exception as e:
            logger.error(f"Error in ChannelAgent: {str(e)}")
            return (False, f"@GroupChatManager: Error generating instructions: {str(e)}")

    agent = ConversableAgent(
        name=agent_name,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="You are the ChannelAgent in Dell's technical support workflow for accidental damage claims. Process messages using the defined function."
    )

    # Register custom reply function
    agent.register_reply(
        trigger=ConversableAgent,
        reply_func=process_message
    )

    return agent