# from autogen import ConversableAgent
# import logging

# logger = logging.getLogger(__name__)

# def create_decision_orchestrator(llm_config):
#     return ConversableAgent(
#         name="DescisionOrchestrator",
#         llm_config=llm_config,
#         system_message="""You are the DecisionOrchestrator in a multi-agent system within Dell's technical support workflow. Your sole responsibility is to provide the final eligibility decision for accidental damage (AD) claims based on inputs from other agents.

# ### ROLE DESCRIPTION
# - You are the FINAL DECISION-MAKER.
# - You DO NOT analyze images or check customer entitlements yourself.
# - You SYNTHESIZE information provided by the below agents based on the scenario:
#   - @ChannelAgent (image status)
#   - @EntitlementAnalyzer (entitlement details)
#   - @DamageAnalyzer (damage classification)
# - You follow Dell's AD policies, warranty rules, and internal decision matrices strictly.

# ### INPUT SCENARIOS
# There are two possible input scenarios:

# **Scenario 1: VL_STATUS = NO_IMAGE_FOUND**
# - Input includes only: "@ChannelAgent's full response"
# - ACTION: Request image upload with exact instructions from ChannelAgent

# **Scenario 2: VL_STATUS = IMAGE_PROCESSED**
# - Input includes:
#   - "@EntitlementAnalyzer’s response" (customer eligibility)
#   - "@DamageAnalyzer’s response" (damage classification)
# - ACTION: Make a final claim decision based on these two inputs.

# ### WORKFLOW RULES
# - You ONLY respond when explicitly prompted by @GroupChatManager.
# - You SPEAK ONCE per conversation cycle.
# - If the prompt is invalid (missing required data), reply with:
#     @GroupChatManager:
#     Invalid prompt. Expected [list missing fields].
# - Do NOT interact with any agent other than @GroupChatManager.
# - If called out of turn, log and ignore: "Unexpected call, waiting for GroupChatManager."

# ### OUTPUT FORMAT (Scenario 1 Only)
# @GroupChatManager:
# ===================== FINAL DECISION REPORT =====================
# Service Tag: [service_tag]
# Visual Listening Analysis: [channelagent response]
# Decision: [Not Eligibile ]
# Rationale: [clear, concise reasoning based on inputs and decision]
# Documents Consulted: [list relevant documents if available]
# ===================== END REPORT =====================


# ### OUTPUT FORMAT (Scenario 2 Only)
# @GroupChatManager:
# ===================== FINAL DECISION REPORT =====================
# Service Tag: [service_tag]
# Damage Assessment: [damage_classification]
# Entitlement Status: [eligible/not eligible]
# Decision: [Eligible / Not Eligibile ]
# Rationale: [clear, concise reasoning based on inputs]
# Documents Consulted: [list relevant documents if available]
# ===================== END REPORT =====================

# TERMINATE


# ### SPECIAL INSTRUCTIONS FOR LLAMA3.1
# - Be precise and avoid speculative language unless instructed.
# - Use bullet-style clarity for rationale.
# - Always end with `TERMINATE` after your report.
# - Avoid markdown formatting. Use plain text with clear separators.

# """
#     )












































from autogen import ConversableAgent
import logging
import asyncio

logger = logging.getLogger(__name__)

class DecisionOrchestratorAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            system_message="""You are the DecisionOrchestrator for Dell Technical Support. Your role is to make the final decision based on inputs from other agents (ChannelAgent, EntitlementAnalyzer, DamageAnalyzer, RetrievalAgent).

**Responsibilities**:
- Analyze inputs from other agents.
- Provide a final decision in the specified format.
- Ensure decisions align with Dell's support policies.

**Output Format**:
@GroupChatManager:
===================== FINAL DECISION REPORT ==================
Service Tag: <service_tag>
Visual Listening Analysis: <vl_analysis>
Decision: <Eligible/Not Eligible>
Rationale: 
- <reason_1>
- <reason_2>
Documents Consulted: <document_list>
===================== END REPORT ==================
TERMINATE
""",
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=False
        )
        self.register_reply(
            [ConversableAgent, None],
            reply_func=self.generate_reply,
            ignore_async_in_sync_chat=True
        )

    async def make_decision(self, messages):
        """Make a final decision based on agent inputs."""
        try:
            service_tag = "Unknown"
            vl_analysis = "No analysis available"
            decision = "Not Eligible"
            rationale = []
            documents = []

            for message in messages:
                content = message.get("content", "")
                if "Service Tag:" in content:
                    service_tag = content.split("Service Tag:")[1].split("\n")[0].strip()
                if "VL Model Output:" in content:
                    vl_analysis = content.split("VL Model Output:")[1].split("\n")[0].strip()
                if "Documents Consulted:" in content:
                    doc_line = content.split("Documents Consulted:")[1].strip()
                    documents = [doc.strip() for doc in doc_line.split(",") if doc.strip()]
                if "Please provide image upload instructions" in content:
                    rationale.append("No image provided; customer must upload images using provided instructions.")

            if "no image" in vl_analysis.lower() or "invalid format" in vl_analysis.lower():
                decision = "Not Eligible"
                if not rationale:
                    rationale.append("No valid image provided for analysis.")

            return f"""@GroupChatManager:
===================== FINAL DECISION REPORT ==================
Service Tag: {service_tag}
Visual Listening Analysis: {vl_analysis}
Decision: {decision}
Rationale: 
- {rationale[0] if rationale else "Insufficient data for decision"}
Documents Consulted: {', '.join(documents) if documents else 'None'}
===================== END REPORT ==================
TERMINATE"""
        except Exception as e:
            logger.error(f"Error in make_decision: {e}")
            return f"Error generating decision: {e}\nTERMINATE"

    async def generate_reply(self, messages, sender, config=None):
        """Generate a reply based on messages."""
        logger.debug(f"DecisionOrchestrator received messages: {messages}")
        if not messages:
            return False, "No messages received"

        last_message = messages[-1].get("content", "")
        if "Service Tag" in last_message or "image upload instructions" in last_message:
            decision = await self.make_decision(messages)
            return True, decision
        return False, None

def create_decision_orchestrator(llm_config):
    return DecisionOrchestratorAgent(name="DecisionOrchestrator", llm_config=llm_config)