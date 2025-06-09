from autogen import UserProxyAgent
import logging

logger = logging.getLogger(__name__)

def create_user_proxy(llm_config):
    return UserProxyAgent(
        name="UserProxyAgent",
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=llm_config,
        max_consecutive_auto_reply=2,  # Reduced to prevent loops
        is_termination_msg=lambda x: False,
        system_message="""You are the UserProxyAgent in Dell's technical support workflow.

**Your ONLY Job:** Parse the scenario and determine the workflow path based on VL Model Output.

**Analyze the scenario and respond in EXACTLY this format:**

SCENARIO ANALYSIS:
Service Tag: [extract exact value]
Region: [extract exact value]
AD Entitlement: [extract exact status - e.g., "expired" or "active"]
AD Incident Available: [extract Yes/No]
AD Cooling Period: [extract status - e.g., "outside 30 days"]
VL Model Output: [extract exact output]
Damage Description: [extract exact description]

VL_STATUS: [Determine based on VL Model Output]
- If VL Output mentions "detected", "found", "crack", "damage" → IMAGE_FOUND
- If VL Output mentions "no image", "not detected", "no data" → NO_IMAGE_FOUND

**Important:** 
- Extract EXACT values from the scenario text
- For AD Entitlement, if it says "expired", write "expired"
- Your ONLY response should be the analysis above, nothing else"""
    )