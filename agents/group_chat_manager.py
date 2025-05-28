from autogen import GroupChat, GroupChatManager
import logging
import re

logger = logging.getLogger(__name__)

def create_group_chat_manager(group_chat, llm_config):
    def custom_speaker_selection(last_speaker, groupchat):
        messages = groupchat.messages
        print(f"Custom speaker selection: last_speaker={last_speaker.name}, messages={len(messages)}")
        if not messages:
            return groupchat.agents[0]  # UserProxyAgent
        last_message = messages[-1].get("content", "")
        if last_speaker.name == "UserProxyAgent":
            return groupchat.agents[1]  # ChannelAgent
        elif last_speaker.name == "ChannelAgent":
            if "@ChannelAgent_RetrievalAgent" in last_message:
                return groupchat.agents[2]  # RetrievalAgent
            elif "Upload Instructions" in last_message or "Error:" in last_message:
                return groupchat.agents[3]  # DecisionOrchestrator
        elif last_speaker.name == "ChannelAgent_RetrievalAgent":
            return groupchat.agents[1]  # ChannelAgent
        elif last_speaker.name == "DecisionOrchestrator":
            return None  # Terminate
        logger.warning(f"Unexpected state: last_speaker={last_speaker.name}, message={last_message[:50]}")
        return None  # Terminate on error

    group_chat.speaker_selection_method = custom_speaker_selection
    return GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        system_message="""You are the GroupChatManager for Dell Technical Support, coordinating a multi-agent workflow for accidental damage claims using a local Llama model. Enforce Scenario 1 (NO_IMAGE_FOUND).

**Workflow**:
1. UserProxyAgent initiates with Service Tag, Region, VL Model Output.
2. ChannelAgent requests chunks from RetrievalAgent.
3. RetrievalAgent fetches chunks.
4. ChannelAgent processes chunks and responds.
5. DecisionOrchestrator generates final report.
6. Terminate on "TERMINATE".

**Rules**:
- Sequence: UserProxyAgent → ChannelAgent → RetrievalAgent → ChannelAgent → DecisionOrchestrator.
- Validate ChannelAgent response: Must include 'Upload Instructions' or error.
- Log invalid responses: "Invalid response from <agent_name>: <reason>"
"""
    )