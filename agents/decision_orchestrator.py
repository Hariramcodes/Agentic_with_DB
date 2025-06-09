from autogen import ConversableAgent
import logging

logger = logging.getLogger(__name__)

def create_decision_orchestrator(llm_config, user_input=None):
    """Create decision orchestrator that handles both entitlement and damage analysis"""
    
    system_message = """You are DecisionOrchestrator for Dell's technical support workflow.

Your job: Make the final support decision based on BOTH entitlement analysis AND damage analysis.

**IMPORTANT:** Wait until you receive analysis from BOTH:
1. EntitlementAnalyzer (with "ENTITLEMENT ANALYSIS COMPLETE")
2. DamageAnalyzer (with "DAMAGE ANALYSIS COMPLETE")

Only after receiving BOTH analyses, respond with this exact format:

**FINAL DECISION:**

Service Tag: [from scenario]
Region: [from scenario]
AD Entitlement: [from EntitlementAnalyzer]
Damage Assessment: [from DamageAnalyzer]
VL Detection: [from scenario]

**COMBINED ANALYSIS:**
Entitlement Status: [summarize entitlement decision and reasoning]
Damage Coverage: [summarize damage decision and reasoning]

**FINAL RECOMMENDATION:**
Work Order Status: [APPROVED/DENIED/REQUIRES_REVIEW]
Customer Action: [what the customer should do next]
Reasoning: [combined reasoning from both analyses]

**CONVERSATION COMPLETE.**

**CRITICAL RULES:**
- Do NOT respond until you have received BOTH analyzer outputs
- Base your decision on BOTH entitlement eligibility AND damage coverage
- If either analysis is missing, wait for it
- Consider both factors in your final recommendation"""

    logger.info("Creating DecisionOrchestrator for dual analyzer workflow")

    return ConversableAgent(
        name="DecisionOrchestrator",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=1,
        is_termination_msg=lambda x: False  # NEVER terminate on message content
    )