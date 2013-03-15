class StateValidationError(Exception):
    """
    An exception to indicate that the transition failed validation and will not be committed.
    """
    pass


class TransitionValidationError(Exception):
    """
    An exception to indicate that the transition failed validation and will not be committed.
    """
    pass


class TransitionFatalError(Exception):
    """
    An unrecoverable error occured during a transition, most likely leaving the transition in a half-committed state.
    """


class TransitionActionError(Exception):
    """
    An exception to indicate that the action failed validation and will not be enacted.
    """
    pass
