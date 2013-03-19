from errors import TransitionValidationError
from transition_parameter import TransitionParameter


class TrackingItem(object):
    def __init__(self):
        self.validations = []

    def validate(self):
        """
        Apply each rule to the item and only succeed if all validations pass.
        """
        import operator
        return reduce(operator.and_, map(lambda f: f(self), self.validations), True)

    def export(self):
        """
        TrackingItems export themself to the world as a dict, so external consumers can determine their properties.
        """
        item_dict = self.__dict__.copy()
        item_dict.pop("validations")
        return item_dict


class TransitionValidationResult(object):
    """
    The result of each validation step in a transition's action.
    If unsuccessful, the failure message can be checked for a reason.
    """

    def __init__(self, success, failure_message):
        self.success = success
        self.message = failure_message
        self.parameters = {}

    def succeeded(self):
        return self.success is True

    def add_parameter(self, name, value):
        self.parameters.update({name: value})


class TrackingState(object):
    def __init__(self, name, item_type):
        self.name = name
        self.item_type = item_type

    def _validated_item(self, item_dict, parameters=None):
        parameters = parameters if parameters else {}
        unvalidated_params = {v.name: k for k, v in item_dict.iteritems() if isinstance(v, TransitionParameter)}

        for name, value in parameters.iteritems():
            item_dict.update({unvalidated_params[name]: value})

        item = self.item_type(item_dict)
        return item if item.validate() else None

    def track(self, item, dry_run=None):
        """
        Track an item in this state.
        An item cannot be 'untracked', items only move between states via transitions.
        Item may either be a dictionary, or an item if being called internally.
        If a dictionary, we must perform any necessary validations before tracking is allowed.
        Do not override, see _track method instead.
        """
        if not isinstance(item, self.item_type):
            item = self._validated_item(item)
        if not item:
            raise TransitionValidationError("Could not validate item {0} to track it.".format(item))

        dry_run = True if dry_run is not None else False
        for validation in self._track(item):
            if not validation.succeeded():
                raise TransitionValidationError(validation.message)
            elif dry_run:
                return True

        return True

    def _track(self, item):
        """
        Internal track method all implementors provide.
        """
        raise NotImplementedError()  # pragma: no cover

    def quantity(self, key=None):
        """
        Quantity of items tracked, most implementors will have additional keys to filter on.
        """
        raise NotImplementedError()  # pragma: no cover

    def get(self, key):
        obj = self._get(key)
        if obj:
            if isinstance(obj, list):
                return map(lambda o: o.export(), obj)
            else:
                return obj.export()
        else:
            return None

    def _get(self, key):
        """
        Internal get method to retrieve a tracked item by specified key.
        """
        raise NotImplementedError()  # pragma: no cover
