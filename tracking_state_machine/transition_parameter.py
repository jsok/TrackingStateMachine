class TransitionParameter(object):
    """
    A Transition Parameter defines the communication protocol between the "from" state to the "to" state.
    The "to" state declares its unknown item parameters with a name which will be matched with any parameters
    emitted by the "from" state.
    The "to" state can optionally define a default value if the "from" state never emits the required parameter.
    If the "to" state does not define a default and no value is returned by the "from" state an exception will be
    raised and treated as a TransitionValidationError.
    The "from" state can use the same value argument to communicate back to the "to" state its value.
    """

    def __init__(self, name, value=None):
        self.name = name
        self.value = value if value else None
