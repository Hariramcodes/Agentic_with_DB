from autogen import ConversableAgent
import logging

logger = logging.getLogger(__name__)

def create_channel_agent(llm_config, agent_name="ChannelAgent"):
    return ConversableAgent(
        name=agent_name,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="""You are the ChannelAgent for Dell's technical support workflow. You handle image upload instructions.

**FIRST RESPONSE** - Request Document Retrieval:
When you receive a message with "VL_STATUS: NO_IMAGE_FOUND", extract the region and respond EXACTLY:

@ChannelAgent_RetrievalAgent: Fetch chunks for VL.pdf with query: location [REGION] language [LANGUAGE]

**SECOND RESPONSE** - Process Retrieved Chunks:
When you receive "Retrieved chunks:" from RetrievalAgent, respond EXACTLY:

@GroupChatManager:
VL Output: [original_vl_output]
Upload Instructions:
Customer Location: [region]
Language: [language]

CHUNKS RECEIVED: [number] chunks processed

Available Upload Channels:
[Extract key upload methods from chunks - WhatsApp, Email, etc.]

Contact Information:
[Extract contact details from chunks]

Requirements:
- Include Service Tag [service_tag] in communications
- Upload clear JPEG/PNG images
- Follow regional procedures

Documents Consulted: VL.pdf

**Keep responses concise and fast.**"""
    )