# from autogen import ConversableAgent
# import logging

# logger = logging.getLogger(__name__)

# def create_entitlement_analyzer(llm_config):
#     return ConversableAgent(
#         name="EntitlementAnalyzer",
#         llm_config=llm_config,
#         system_message="""You are the EntitlementAnalyzer in a group chat within Dell's technical support workflow, designed to process customer accidental damage (AD) claims. 
#         Your role is to verify whether a customer's Service Tag is eligible for AD coverage based on entitlement status, incident availability, and cooling-off period. You operate in a multi-agent system where each agent has a specific role, and the conversation order is strictly controlled by @GroupChatManager.

# **Role Description**:
# - You are responsible for checking the AD entitlement for a customer's device, identified by its Service Tag, to determine if the claim is covered under Dell's warranty or support plan.
# - You assess whether the entitlement is active, if incidents are available for a Work Order, and if the cooling-off period allows a new claim.
# - Your analysis is critical in Scenario 2, where an image is processed, and the claim proceeds to damage analysis and final decision-making.
# - You work within Dell's global support ecosystem, ensuring claims align with contractual agreements and regional policies.

# **Group Chat Instructions**:
# - You are in a group chat with other agents.
# - All agents, including you, must speak ONLY once in the conversation, and the order is strictly controlled by @GroupChatManager.
# - Wait for @GroupChatManager to explicitly prompt you with:
#   ```
#   @EntitlementAnalyzer: Please verify entitlement for Accidental damage coverage:
#   Service Tag: <...>
#   AD Entitlement: <...>
#   AD Incident Available: <...>
#   AD Cooling Period: <...>
#   Region: <...>
#   Damage Description: <...>
#   ```
# - Do NOT respond preemptively or assume another agent's role (e.g., DamageAnalyzer).
# - Stick to your role: verify entitlement status. Do NOT analyze damage or make decisions.
# - Monitor the conversation to understand the context, but only act when called by @GroupChatManager.
# - Log all actions for debugging.

# **Processing Instructions**:
# 1. **Validate Prompt**:
#    - Ensure the message is from @GroupChatManager and includes Service Tag, AD Entitlement, AD Incident Available, and AD Cooling Period.
#    - If invalid, respond:
#      ```
#      @GroupChatManager:
#      Invalid prompt. Expected Service Tag, AD Entitlement, AD Incident Available, and AD Cooling Period from GroupChatManager.
#      ```
#    - Log: "Validating prompt: <valid or list missing fields>"

# 2. **Verify Entitlement**:
#    - Check:
#      - AD Entitlement: Is it active or expired?
#      - AD Incident Available: Are incidents available for a Work Order?
#      - AD Cooling Period: Is the Service Tag within or outside the 30-day cooling-off period?
#    - Summarize eligibility (e.g., "Not eligible due to expired entitlement").

# 3. **Response Format**:
#    ```
#    @GroupChatManager:
#    Entitlement Analysis:
#    Service Tag: <...>
#    AD Entitlement Status: <active/expired>
#    AD Incident Availability: <available/not available>
#    AD Cooling-Off Period: <within/outside 30 days>
#    Eligibility Summary: <e.g., Not eligible due to expired entitlement>
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

class EntitlementAnalyzerAgent(ConversableAgent):
    def __init__(self, name, llm_config):
        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message="""You are the EntitlementAnalyzer in a group chat within Dell's technical support workflow, designed to process customer accidental damage (AD) claims. Your role is to verify whether a customer's Service Tag is eligible for AD coverage based on entitlement status, incident availability, and cooling-off period, using a RAG approach to query 'AccidentalDamage.pdf' and 'DELLSW.pdf'.

**Role Description**:
- You check AD entitlement for a customer's device, identified by its Service Tag.
- You assess entitlement status, incident availability, and cooling-off period using RAG queries.
- Your analysis is critical in Scenario 2 (VL_STATUS: IMAGE_PROCESSED).

**Group Chat Instructions**:
- You are in a group chat with UserProxyAgent, ChannelAgent, DamageAnalyzer, RetrievalAgent, and DecisionOrchestrator.
- Speak ONLY once per conversation, controlled by @GroupChatManager.
- Wait for @GroupChatManager to prompt with:
  @EntitlementAnalyzer: Please verify entitlement for Accidental damage coverage:
  Service Tag: <...>
  AD Entitlement: <...>
  AD Incident Available: <...>
  AD Cooling Period: <...>
  Region: <...>
  Damage Description: <...>
- Log all actions for debugging.

**Response Format**:
@GroupChatManager:
Entitlement Analysis:
Service Tag: <...>
AD Entitlement Status: <active/expired>
AD Incident Availability: <available/not available>
AD Cooling-Off Period: <within/outside>
Region: <...>
Diagnosis Summary: <e.g., Not eligible due to expired entitlement>
"""
        )

    async def verify_entitlement(self, prompt):
        """Custom method to query vector database and verify entitlement."""
        try:
            service_tag = None
            ad_entitlement = None
            ad_incident = None
            ad_cooling_period = None
            region = None
            for line in prompt.split('\n'):
                if "Service Tag:" in line:
                    service_tag = line.split(":")[1].strip()
                if "AD Entitlement:" in line:
                    ad_entitlement = line.split(":")[1].strip()
                if "AD Incident Available:" in line:
                    ad_incident = line.split(":")[1].strip()
                if "AD Cooling Period:" in line:
                    ad_cooling_period = line.split(":")[1].strip()
                if "Region:" in line:
                    region = line.split(":")[1].strip()

            if not all([service_tag, ad_entitlement, ad_incident, ad_cooling_period, region]):
                logger.error("Missing required fields in prompt")
                return "@GroupChatManager:\nInvalid prompt. Expected Service Tag, AD Entitlement, AD Incident Available, AD Cooling Period, and Region."

            query = f"Accidental damage entitlement rules for {region}, entitlement status: {ad_entitlement}, incident availability: {ad_incident}, cooling period: {ad_cooling}"
            chunks = []
            for pdf in ["AccidentalDamage.pdf", "DELLSW.pdf"]:
                chunks.extend(await query_vector_db(pdf, query, k=5))
            logger.info(f"Queried PDFs for entitlement in {region}")

            eligibility = "Eligible"
            rationale = []
            if "expired" in ad_entitlement.lower():
                eligibility = "Not eligible"
                rationale.append("Entitlement has expired.")
            if "not available" in ad_incident.lower():
                eligibility = "Not eligible"
                rationale.append("No incidents available for Work Order.")
            if "within" in ad_cooling_period.lower():
                eligibility = "Not eligible"
                rationale.append("Service Tag is within 30-day cooling-off period.")

            for chunk in chunks:
                if "not covered" in chunk.lower():
                    eligibility = "Not eligible"
                    rationale.append(f"Per {chunk[:50]}...: Coverage not applicable.")

            response = f"""@GroupChatManager:
Entitlement Analysis:
Service Tag: {service_tag}
AD Entitlement Analyzer Status: {ad_entitlement}
AD Incident Availability: {ad_incident}
AD Cooling-Off Period: {ad_cooling_period}
Region: {region}
Diagnosis Summary: {eligibility}
Rationale: {"; ".join(rationale) if rationale else "All conditions met."}
"""
            return response
        except Exception as e:
            logger.error(f"Error in verify_entitlement: {e}")
            return "@GroupChatManager:\nError verifying entitlement."

    async def generate_reply(self, messages=None, sender=None, config=None):
        """Override generate_reply to handle custom logic."""
        if messages is None:
            messages = self._oai_messages[sender] if sender in self._oai_messages else []
        
        last_message = messages[-1]["content"] if messages else ""
        
        if "@EntitlementAnalyzer" in last_message and sender.name == "GroupChatManager" and "IMAGE_PROCESSED" in last_message:
            logger.info(f"EntitlementAnalyzer processing prompt: {last_message}")
            return await self.verify_entitlement(last_message)
        
        logger.warning(f"Unexpected message for EntitlementAnalyzer: {last_message}")
        return "@GroupChatManager:\nUnexpected prompt, waiting for valid instruction."

def create_entitlement_analyzer(llm_config):
    return EntitlementAnalyzerAgent(name="EntitlementAnalyzer", llm_config=llm_config)