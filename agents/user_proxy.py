from autogen import ConversableAgent
import logging
import re

logger = logging.getLogger(__name__)

class AnalysisAgent(ConversableAgent):
    def __init__(self, llm_config):
        super().__init__(
            name="UserProxyAgent",
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config,
            max_consecutive_auto_reply=1,
            is_termination_msg=lambda x: False,
            system_message="""You are the UserProxyAgent in Dell's technical support workflow.

MANDATORY TASK: Analyze the scenario and determine VL_STATUS.

When you receive scenario details, you MUST respond with analysis in this EXACT format:

SCENARIO ANALYSIS:
Service Tag: [extract value]
Region: [extract value]
AD Entitlement: [extract status]
AD Incident Available: [extract Yes/No]
AD Cooling Period: [extract status]
VL Model Output: [copy exact text]
Damage Description: [extract description]

VL_STATUS: [determine based on VL Model Output]

VL_STATUS RULES:
- If VL Model Output contains "did not detect" OR "no image" OR "no data found" → VL_STATUS: NO_IMAGE_FOUND
- If VL Model Output contains "detected" OR "found" OR "crack" OR "damage" → VL_STATUS: IMAGE_FOUND

You MUST analyze and provide VL_STATUS determination."""
        )
    
    def generate_reply(self, messages=None, sender=None, **kwargs):
        """Override to force analysis of scenario"""
        if messages and len(messages) > 0:
            last_msg = messages[-1]["content"]
            
            # Check if this is a scenario input (not already analyzed)
            if "Scenario details:" in last_msg and "VL_STATUS:" not in last_msg:
                # Extract VL Model Output to determine status
                vl_output_match = re.search(r'VL Model Output: (.*)', last_msg)
                if vl_output_match:
                    vl_output = vl_output_match.group(1)
                    
                    # Determine VL_STATUS based on output
                    if any(phrase in vl_output.lower() for phrase in ["did not detect", "no image", "no data found", "not detected", "not in proper format"]):
                        vl_status = "NO_IMAGE_FOUND"
                    elif any(phrase in vl_output.lower() for phrase in ["detected", "found", "crack", "damage", "lcd", "screen"]):
                        vl_status = "IMAGE_FOUND"
                    else:
                        vl_status = "NO_IMAGE_FOUND"  # Default for unclear cases
                    
                    # Extract other details
                    service_tag = re.search(r'Service Tag: (\w+)', last_msg)
                    region = re.search(r'Region: (\w+)', last_msg)
                    ad_entitlement = re.search(r'AD Entitlement: (.*)', last_msg)
                    ad_incident = re.search(r'AD Incident Available: (.*)', last_msg)
                    cooling_period = re.search(r'AD Cooling Period: (.*)', last_msg)
                    damage_desc = re.search(r'Damage Description: (.*)', last_msg)
                    
                    # Format analysis response
                    analysis = f"""SCENARIO ANALYSIS:
Service Tag: {service_tag.group(1) if service_tag else 'Unknown'}
Region: {region.group(1) if region else 'Unknown'}
AD Entitlement: {ad_entitlement.group(1) if ad_entitlement else 'Unknown'}
AD Incident Available: {ad_incident.group(1) if ad_incident else 'Unknown'}
AD Cooling Period: {cooling_period.group(1) if cooling_period else 'Unknown'}
VL Model Output: {vl_output}
Damage Description: {damage_desc.group(1) if damage_desc else 'Unknown'}

VL_STATUS: {vl_status}"""
                    
                    return True, analysis
        
        # Fallback to normal generation
        return super().generate_reply(messages, sender, **kwargs)

def create_user_proxy(llm_config):
    return AnalysisAgent(llm_config)