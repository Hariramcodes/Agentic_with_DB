from autogen import ConversableAgent
import logging

logger = logging.getLogger(__name__)

def create_user_proxy(llm_config):
    return ConversableAgent(
        name="UserProxyAgent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        system_message="""You are the UserProxyAgent in Dell's technical support workflow. You receive initial input and process it.

When you receive input with Service Tag, Region, and VL Model Output, respond EXACTLY:

VL_STATUS: NO_IMAGE_FOUND
Service Tag: [service_tag]
Region: [region]  
VL Model Output: [vl_output]

That's it. Keep it simple and short. Don't add extra text or @mentions."""
    )