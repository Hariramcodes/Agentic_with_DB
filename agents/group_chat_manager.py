from autogen import GroupChatManager
import logging

logger = logging.getLogger(__name__)

def create_group_chat_manager(group_chat, llm_config):
    def custom_select_speaker(self, last_speaker, groupchat):
        try:
            messages = groupchat.messages
            logger.info(f"Custom speaker selection: last_speaker={last_speaker.name}, messages={len(messages)}")

            # Get allowed transitions
            allowed_speakers = groupchat.allowed_or_disallowed_speaker_transitions.get(last_speaker, [])

            if not allowed_speakers:
                logger.warning("No allowed speakers for transition")
                return None

            # Select next speaker based on message content
            last_message = messages[-1]["content"] if messages else ""
            for speaker in allowed_speakers:
                if f"@{speaker.name}" in last_message:
                    logger.info(f"Selected speaker: {speaker.name}")
                    return speaker

            # Default to first allowed speaker
            selected = allowed_speakers[0]
            logger.info(f"Default selected speaker: {selected.name}")
            return selected
        except Exception as e:
            logger.error(f"Error in select_speaker: {str(e)}")
            return None

    # Create GroupChatManager
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False
    )

    # Override select_speaker
    manager.select_speaker = custom_select_speaker.__get__(manager, GroupChatManager)

    # Override run_chat to handle responses
    def custom_run_chat(self, messages=None, sender=None, config=None):
        try:
            messages = messages or self.groupchat.messages
            logger.info(f"Running chat with {len(messages)} messages")
            for _ in range(self.groupchat.max_round):
                last_speaker = sender if sender else self.groupchat.agents[0]
                next_speaker = self.select_speaker(last_speaker, self.groupchat)
                if not next_speaker:
                    logger.warning("No next speaker selected")
                    break

                # Get reply
                reply = next_speaker.generate_reply(messages=messages, sender=last_speaker)
                logger.info(f"Received reply from {next_speaker.name}: type={type(reply)}, content={str(reply)[:100]}...")

                # Handle different reply formats
                is_termination = False
                if isinstance(reply, tuple) and len(reply) == 2:
                    is_termination, message = reply
                elif isinstance(reply, dict) and "content" in reply:
                    message = reply["content"]
                else:
                    message = reply

                # Append message
                messages.append({"content": message, "role": "assistant", "name": next_speaker.name})
                self.groupchat.messages = messages

                # Check for termination
                if is_termination or "TERMINATE" in message:
                    logger.info("Termination signal received")
                    break
            return messages
        except Exception as e:
            logger.error(f"Error in run_chat: {str(e)}")
            raise

    manager.run_chat = custom_run_chat.__get__(manager, GroupChatManager)
    return manager