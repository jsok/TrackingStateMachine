from errors import StateValidationError, TransitionActionError, TransitionFatalError, TransitionValidationError
from tracking_state import TrackingState


class TrackingStateMachine(object):
    def __init__(self):
        self.states = {}
        self.transitions = {}
        self.actions = {}

    def state(self, name):
        return self.states.get(name, None)

    def add_state(self, state):
        if not isinstance(state, TrackingState):
            raise StateValidationError("Provided state is not a TrackingState.")
        self.states.update({state.name: state})

    def transition(self, name, from_item_dict, to_item_dict, dry_run=None):
        """
        Retrieve the transition function and curry in the to_state.
        Validate the items being passed into each state.
        """
        if name not in self.transitions:
            raise TransitionValidationError("Unknown transition: {0}".format(name))
        from_state, to_state = self.transitions.get(name)

        from_item = from_state._validated_item(from_item_dict)
        if not from_item:
            raise TransitionValidationError("Could not validate {0}".format(from_item_dict))

        # Perform all pre-transition validations on initiating state
        transition = getattr(from_state, name)(from_item)
        validation_parameters = {}
        for validation in transition:
            if not validation.succeeded():
                raise TransitionValidationError(validation.message)
            else:
                validation_parameters = validation.parameters
                break  # Halt

        # Update any TransitionParameters with their values and validate to_item
        to_item = to_state._validated_item(to_item_dict, parameters=validation_parameters)
        if not to_item:
            raise TransitionValidationError("Could not validate {0}".format(to_item_dict))

        # Ensure receiving state is able to track item
        track = to_state._track(to_item)
        for validation in track:
            if not validation.succeeded():
                raise TransitionValidationError(validation.message)
            else:
                break  # Halt

        dry_run = True if dry_run else False
        if not dry_run:
            # Run to completion
            for validation in transition:  # pragma: no cover
                if validation:
                    raise TransitionFatalError("Transition from-state encountered fatal error")
            for validation in track:  # pragma: no cover
                if validation:
                    raise TransitionFatalError("Transition to-state encountered fatal error")

        return True

    def add_transition(self, name, from_state, to_state):
        """
        Add a transition between two states.
        The name is taken to be a method on the from_state.
        """
        from_state = self.states.get(from_state, None)
        to_state = self.states.get(to_state, None)

        for state in [from_state, to_state]:
            if not state:
                raise StateValidationError("State {0} does not exist.".format(state))

        if hasattr(from_state, name) and callable(getattr(from_state, name)):
            self.transitions.update({name: (from_state, to_state)})
        else:
            raise TransitionValidationError("State {0} does not define transition {1}".format(from_state, name))

    def action(self, name, args):
        """
        Perform an action which is limited in scope within the state.
        Args is a dict of arguments to pass to the action, validation is the responsibility of the state.
        """
        import functools

        state = self.actions.get(name, None)
        if not state:  # pragma: no cover
            raise TransitionActionError("Unknown action: {0}".format(name))
        action = getattr(state, name)
        return functools.partial(action, args)

    def add_action(self, name, state):
        """
        Add an action to a state.
        The name is taken to be a method on the state.
        """
        state = self.states.get(state, None)
        if not state:
            raise StateValidationError("State {0} does not exist.".format(state))

        if hasattr(state, name):
            self.actions.update({name: state})
        else:
            raise TransitionActionError("State {0} does not define action {1}".format(state, name))