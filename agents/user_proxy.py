from autogen import ConversableAgent
import logging

logger = logging.getLogger(__name__)

def create_user_proxy(llm_config):
    return ConversableAgent(
        name="UserProxyAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="""You are the UserProxyAgent in Dell's technical support workflow. Your role is to validate input and initiate the channel agent workflow when no image is available.

**Your Task**:
1. Extract Service Tag, Region, and VL Model Output from the incoming message
2. Analyze the VL Model Output to determine if an image was successfully processed
3. If the VL output indicates no image (contains phrases like "no image", "not found", "invalid", "not available"), initiate the channel agent workflow

**Response Format** (when no image detected):
@GroupChatManager:
VL_STATUS: NO_IMAGE_FOUND
Service Tag: [extracted_service_tag]
Region: [extracted_region]
VL Model Output: [extracted_vl_output]

Initiating Channel Agent workflow for image upload instructions.

**Guidelines**:
- Only respond once to initiate the workflow
- Extract information exactly as provided in the input
- Be precise in detecting when no valid image was processed
- Use the exact format shown above"""
    )