"""
This module contains the different action classes that can be returned by the interaction functions.
"""
from abc import ABC
from enum import Enum
import time

class ActionType(str, Enum):
    """ An enumeration of the different action types. """

    DEFER = "defer"
    SEND = "send"
    DELETE = "delete"
    EDIT = "edit"
    CREATE_REACTION = "create_reaction"
    SEND_MODAL = "send_modal"
    SEND_CHOICES = "send_choices"


class BaseAction(ABC):
    """ The base action class.  """

    action_type: ActionType
    creation_time: float

    def __init__(self):
        self.creation_time = time.time_ns()


class DeferAction(BaseAction):
    """ The defer action class with ephemeral attribute. """
    action_type = ActionType.DEFER
    ephemeral: bool

    def __init__(self, ephemeral: bool):
        super().__init__()
        self.ephemeral = ephemeral


class SendAction(BaseAction):
    """ The send action class with message attribute. """
    action_type = ActionType.SEND
    message: dict

    def __init__(self, message: dict):
        super().__init__()
        self.message = message


class DeleteAction(BaseAction):
    """ The delete action class with message_id attribute. """
    action_type = ActionType.DELETE
    message_id: int

    def __init__(self, message_id: int):
        super().__init__()
        self.message_id = message_id


class EditAction(BaseAction):
    """ The edit action class with message attribute. """
    action_type = ActionType.EDIT
    message: dict

    def __init__(self, message: dict):
        super().__init__()
        self.message = message


class CreateReactionAction(BaseAction):
    """ The create reaction action class with message_id and emoji attributes. """
    action_type = ActionType.CREATE_REACTION
    message_id: int
    emoji: str

    def __init__(self, message_id: int, emoji: str):
        super().__init__()
        self.message_id = message_id
        self.emoji = emoji


class SendModalAction(BaseAction):
    """ The send modal action class with modal attribute. """
    action_type = ActionType.SEND_MODAL
    modal: dict

    def __init__(self, modal: dict):
        super().__init__()
        self.modal = modal


class SendChoicesAction(BaseAction):
    """ The send choices action class with choices attribute. """
    action_type = ActionType.SEND_CHOICES
    choices: list[dict]

    def __init__(self, choices: list[dict]):
        super().__init__()
        self.choices = choices
