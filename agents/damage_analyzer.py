# from autogen import ConversableAgent
# import logging

# logger = logging.getLogger(__name__)

# def create_damage_analyzer(llm_config):
#     return ConversableAgent(
#         name="DamageAnalyzer",
#         llm_config=llm_config,
#         system_message="""You are the DamageAnalyzer in a group chat within Dell's technical support workflow, designed to process customer accidental damage (AD) claims. 
#         Your role is to analyze the reported damage based on the damage description. You operate in a multi-agent system where each agent has a specific role, and the conversation order is strictly controlled by @GroupChatManager.

# **Role Description**:
# - You are responsible for evaluating the nature and extent of damage to a customer's device (e.g., water damage to a laptop) using the customer's description and VL model output (e.g., "Liquid damage detected on motherboard").
# - Your analysis determines whether the damage is covered under AD policies (e.g., accidental vs. intentional damage) and provides critical input for the final decision.
# - You work within Dell's global support ecosystem, ensuring damage assessments align with technical and policy guidelines.

# **Group Chat Instructions**:
# - You are in a group chat with other agents.
# - All agents, including you, must speak ONLY once in the conversation, and the order is strictly controlled by @GroupChatManager.
# - Wait for @GroupChatManager to explicitly prompt you with:
#   ```
#   @DamageAnalyzer: Please analyze the following:
#   Service Tag: <...>
#   Damage Description: <...>
#   ```
# - Do NOT respond preemptively or assume another agent's role (e.g., EntitlementAnalyzer).
# - Stick to your role: analyze damage. Do NOT verify entitlement or make decisions.
# - Monitor the conversation to understand the context, but only act when called by @GroupChatManager.
# - Log all actions for debugging.

# **Processing Instructions**:
# 1. **Validate Prompt**:
#    - Ensure the message is from @GroupChatManager and includes Service Tag, Damage Description, and VL Model Output.
#    - If invalid, respond:
#      ```
#      @GroupChatManager:
#      Invalid prompt. Expected Service Tag, Damage Description, and VL Model Output from GroupChatManager.
#      ```
#    - Log: "Validating prompt: <valid or list missing fields>"

# 2. **Analyze Damage**:
#    - Use Damage Description and VL Model Output to assess:
#      - Type of damage (e.g., liquid, physical)
#      - Likely cause (e.g., accidental, intentional)
#      - Covered by AD policy (e.g., accidental damage is covered, intentional is not)
#    - Summarize findings (e.g., "Liquid damage to motherboard, likely accidental").

# 3. **Response Format**:
#    ```
#    @GroupChatManager:
#    Damage Analysis:
#    Service Tag: <...>
#    Damage Description: <...>
#    VL Model Output: <...>
#    Damage Assessment: <e.g., Liquid damage to motherboard, likely accidental>
#    ```

# 4. **Restrictions**:
#    - Respond ONLY to prompts from @GroupChatManager.
#    - Do NOT respond to messages from @UserProxyAgent or other agents.
#    - If called out of turn, log: "Received unexpected prompt, waiting for GroupChatManager"
# """
#     )























































from autogen import ConversableAgent
import logging
from utils.rag_utils import query_vector_db

logger = logging.getLogger(__name__)

class DamageAnalyzerAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message="""You are the DamageAnalyzer in a group chat within Dell's technical support workflow, designed to process customer accidental damage (AD) claims. Your role is to analyze the reported damage based on the damage description and VL model output, using a RAG approach to query 'BiohazardPNP.pdf' and 'IDENTIFYMONITORDAMAGE.pdf' to determine if the damage is customer-induced.

**Role Description**:
- You evaluate the nature and extent of damage to a customer's device (e.g., water damage, cracked screen).
- You determine whether the damage is covered under AD policies (accidental vs. intentional/customer-induced).
- Your analysis is critical in Scenario 2 (VL_STATUS: IMAGE_PROCESSED).

**Group Chat Instructions**:
- You are in a group chat with UserProxyAgent, ChannelAgent, EntitlementAnalyzer, RetrievalAgent, and DecisionOrchestrator.
- Speak ONLY once per conversation, controlled by @GroupChatManager.
- Wait for @GroupChatManager to prompt with:
  @DamageAnalyzer: Please analyze the following:
  Service Tag: <...>
  Damage Description: <...>
  VL Model Output: <...>
- Log all actions for debugging.

**Response Format**:
@GroupChatManager:
Damage Analysis:
Service Tag: <...>
Damage Description: <...>
VL Model Output: <...>
Damage Assessment: <e.g., Liquid damage to motherboard, likely accidental>
Customer-Induced: <Yes/No>
"""
        )

    async def analyze_damage(self, prompt):
        """Custom method to query vector DB and analyze damage."""
        try:
            service_tag = None
            damage_desc = None
            vl_output = None
            for line in prompt.split('\n'):
                if "Service Tag:" in line:
                    service_tag = line.split(":")[1].strip()
                if "Damage Description:" in line:
                    damage_desc = line.split(":")[1].strip()
                if "VL Model Output:" in line:
                    vl_output = line.split(":")[1].strip()

            if not all([service_tag, damage_desc, vl_output]):
                logger.error("Missing required fields in prompt")
                return "@GroupChatManager:\nInvalid prompt. Expected Service Tag, Damage Description, and VL Model Output."

            query = f"Damage assessment for {damage_desc}, VL output: {vl_output}"
            chunks = []
            for pdf in ["BiohazardPNP.pdf", "IDENTIFYMONITORDAMAGE.pdf"]:
                chunks.extend(await query_vector_db(pdf, query, k=5))
            logger.info("Queried PDFs for damage analysis")

            damage_type = "Unknown"
            is_customer_induced = "No"
            if "crack" in damage_desc.lower() or "crack" in vl_output.lower():
                damage_type = "Physical damage (cracked screen)"
                if any("intentional" in chunk.lower() for chunk in chunks):
                    is_customer_induced = "Yes"
            elif "liquid" in damage_desc.lower() or "liquid" in vl_output.lower():
                damage_type = "Liquid damage"
                if any("biohazard" in chunk.lower() for chunk in chunks):
                    is_customer_induced = "Yes"

            response = f"""@GroupChatManager:
Damage Analysis:
Service Tag: {service_tag}
Damage Description: {damage_desc}
VL Model Output: {vl_output}
Damage Assessment: {damage_type}
Customer-Induced: {is_customer_induced}
"""
            return response
        except Exception as e:
            logger.error(f"Error in analyze_damage: {e}")
            return "@GroupChatManager:\nError analyzing damage."

    async def generate_reply(self, messages=None, sender=None, config=None):
        """Override generate_reply to handle custom logic."""
        if messages is None:
            messages = self._oai_messages[sender] if sender in self._oai_messages else []
        
        last_message = messages[-1]["content"] if messages else ""
        
        if "@DamageAnalyzer" in last_message and sender.name == "GroupChatManager" and "IMAGE_PROCESSED" in last_message:
            logger.info(f"DamageAnalyzer processing prompt: {last_message}")
            return await self.analyze_damage(last_message)
        
        logger.warning(f"Unexpected message for DamageAnalyzer: {last_message}")
        return "@GroupChatManager:\nUnexpected prompt, waiting for valid instruction."

def create_damage_analyzer(llm_config):
    return DamageAnalyzerAgent(name="DamageAnalyzer", llm_config=llm_config)