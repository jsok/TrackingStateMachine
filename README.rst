===========
Tracking State Machine
===========

A State Machine which can simultaneously track many items in all states and manage transitions.

Requirements
-------------

* Python 2.7

Quickstart
----------

The basic concepts in TSM are:
 * TrackingStateMachine: The manager object which contains all state objects and initiates transitions.
 * TrackingState: A state in the TSM, whose minimal responsibility is to store any objects which are in this state.
 * TrackingItem: A base class for items which will be stored in a state (or states).

Defining States and Items
-------------------------

First we must describe the items we will be storing in each state::

    class Friend(TrackingItem):
        def __init__(self, name, reason):
            super(self.__class__, self).__init__()
            self.name = name
            self.reason


Here we define a simple item which does nothing but store a name, and a reason why we are friends with them.

Next we define a state::

    class FriendshipState(TrackingState):
        def __init__(self, name):
            super(self.__class__, self).__init__(name, Friend)
            self.items = []

        def _track(self, item):
            yield TransitionValidationResult(True, None)
            self.items.append(item)

This is a a trivial state which stores a list of ``Friend`` s which currently exist in it.

The ``_track()`` method tells the TSM what to do with items transitioning into this state.
An important note to make is the ``yield`` statement in ``_track()``::

        yield TransitionValidationResult(True, None)

This exposes some of the design of TSM, specifically that the function of tracking items and performing transitions
are implementing using generators.

Transition Validations
----------------------

As just mentioned, transitions and item tracking are implemented using generators.
TrackingState implementations need to conform to this protocol by:

1. Performing ``yield TransitionValidationResult(True, None)`` to tell TSM that they are ready to commit to the
   transition.

2. If they decide that a transition will break one of their invariants, they can perform:
   ``yield TransitionValidationResult(False, "DO NOT WANT!")``
   to tell TSM that the transition should abort.

A more explicit example, say we never want to track items whose name is "Jonathan", this can be achieved by::

    def _track(self, item):
        if item.name is "Jonathan":
            yield TransitionValidationResult(False, "I don't track Jonathans")

        # I'm happy to accept all other names at this point however
        yield TransitionValidationResult(True, None)
        self.items.append(item)

TrackingItem Validations
------------------------

Checking the name on each track event is a little bit tedious, therefore TSM provides TrackingItem validations too::

    class Friend(TrackingItem):
        def __init__(self, name, reason):
            super(self.__class__, self).__init__()
            self.name = name
            self.reason = reason

            self.validations.extend([
                (lambda item: item.name is not "Jonathan"),
            ])

``TrackingItem.validations`` is a list of lambdas which are applied to the item, if any of them are False, the item is
deemed as invalid.

This validation mechanism is used by TSM automatically, any items which are tracked (explicitly, or implicitly via
a transition) are subject to these validations. Failures will result in transitions being aborted.

Transition vs TrackingItem validations
--------------------------------------

At this point you may wonder which form of validation to use when?

Item validations are useful for:

* Sanitising your items (correct types, presence of values, bounds checks etc.)

Transition validations are useful for:

* Checking for state internal invariants

Say we modify our example and create a "No Jonathans rule", e.g. one Jonathan is fine, two is not::

    class Friend(TrackingItem):
        def __init__(self, name, reason):
            super(self.__class__, self).__init__()
            self.name = name
            self.reason = reason

            self.validations.extend([
                (lambda item: isinstance(item.name, str)),
            ])

    class FriendshipState(TrackingState):
        def __init__(self, name):
            super(self.__class__, self).__init__(name, Friend)
            self.items = []

        def __know_person(self, name):
            # Return index of person if we know them, otherwise None
            for i, person in enumerate(self.items):
                if person.name == name:
                    return i
            return None

        def _track(self, item):
            if self.__know_person("Jonathan"):
                yield TransitionValidationResult(False, "I already know one Jonathan")

            # I'm happy to accept all other names at this point however
            yield TransitionValidationResult(True, None)
            self.items.append(item)

Here we see the guidelines in practise, an item ensures the name is actually a string, but in and of itself,
it has no capacity to check if there exists another item also called Jonathan.

The invariant (only one Jonathan) is enforced in the transition validation.

The State Machine
-----------------

Now that we've defined our state and item, we can describe our state machine.

Let's say we are quite fickle and fall in and out of friendships often::

    tsm = TrackingStateMachine()
    tsm.add_state(FriendshipState("Friend"))
    tsm.add_state(FriendshipState("Enemy"))

To describe how people move between being our Friend and Enemy, we add transitions::

    tsm.add_transition("falling_out", "Friend", "Enemy")
    tsm.add_transition("resolve_differences", "Enemy", "Friend")

However we haven't yet defined in our ``FriendshipState`` how to have a falling out or how to resolve differences.

In general, we say::

    tsm.add_transition(TRANSITION_NAME, FROM_STATE, TO_STATE)

Defining Transitions
--------------------

To define our transitions, we must create methods in the state with the same name as that registered with the TSM::

    class FriendshipState(TrackingState):
        def __know_person(self, name):
            # Return index of person if we know them, otherwise None
            for i, person in enumerate(self.items):
                if person.name == name:
                    return i
            return None

        def __remove_name(self, name):
            known = self.__know_person(name)
            if not known:
                yield TransitionValidationResult(False, "Person {0} is not known to us".format(name))

            # We've made sure person exists and is in this state
            yield TransitionValidationResult(True, None)
            self.items.pop(known)

        def falling_out(self, item):
            return self.__remove_name(item.name)

        def resolve_differences(self, item):
            return self.__remove_name(item.name)

As with all transitions, they must yield a successful transition validation.

Notice, these two transitions are fundamentally identical -- removing the person from the state's internal list of
items. The transition names are simply semantic.

Performing Transitions
----------------------

With the above TSM configuration we can now make friends and enemies!::

    # Declare some people as friends
    friends = [Friend("Jonathan", "I love myself"), Friend("Chris", "Cool dude"), Friend("James", "Nice guy")]

    # We 'track' each friend in the relevant state
    for friend in friends:
        tsm.state("Friends").track(friend)

    # Jonathan annoyed us, he's now an enemy
    tsm.transition("falling_out", Friend("Jonathan", None), Friend("Jonathan", "I hate myself"))

So the way we perform transitions is of the form::

    transition(TRANSITION_NAME, FROM_STATE_ITEM, TO_STATE_ITEM)

When we un-friended Jonathan above, we had to re-create a ``Friend`` object to specify him to each state,
the first time we didn't bother giving a reason because we knew that ``FriendshipState`` isn't interested in the
reason for removing a person.

Dictionary Based Items
----------------------

Performing some transitions immediately exposes some annoyances:

* ``Friend`` items are exposed outside of the TSM.
* We must create ``Friend`` items and know which parameters are useful in which context. e.g. When can I set the
  Friendship reason to ``None``?

To address these two issues, TSM allows dictionary items to be used when performing transitions::

    # Previously, to un-friend Jonathan
    tsm.transition("falling_out", Friend("Jonathan", None), Friend("Jonathan", "I hate myself"))

    # Now with dictionary items
    tsm.transition("falling_out", {"name": "Jonathan"}, {"name": "Jonathan", "reason": "I hate myself"})

However to enable this, we need to change how we init our ``TrackingItem``, in this case ``Friend``::

    class Friend(TrackingItem):
        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.name = properties.get("name")
            self.reason = properties.get("reason")

            self.validations.extend([
                (lambda item: item.name is not None),
            ])

Notice we don't validate the ``reason``, this is because ``reason`` s presence is optional. We actually only care if a
reason is supplied at one point -- when tracking a new ``Friend``, i.e.::

    class FriendshipState(TrackingState):
        def _track(self, item):
            if not item.reason:
                yield TransitionValidationResult(False, "You must supply a reason")

            if "Jonathan" in self.items:
                yield TransitionValidationResult(False, "I already have one Jonathan")

            # I'm happy to accept all other names at this point however
            yield TransitionValidationResult(True, None)
            self.items.append(item)

Transition Parameters
---------------------

Dictionary based items didn't solve one problem:

* We still need to mention **Jonathan** twice in our transition.

If we accidentally mis-typed the name the second time, we could risk never getting our Friend back!

TSM provides a mechanism for the *-from-* state to communicate paramaters to the *-to-* state via
``TransitionParamater`` objects, which can be inserted into dictionary items as follows::

    tsm.transition("falling_out",
                   {"name": "Jonathan"},
                   {"name": TransitionParameter("name"), "reason": "I hate myself"})

What we want to achieve here is to have the *-from-* state fill in the name for us. This requires one small tweak in
how our state transitions::

    class FriendshipState(TrackingState):
        def __remove_name(self, name):
            known = self.__know_person(name)
            if not known:
                yield TransitionValidationResult(False, "Person {0} is not known to us".format(name))

            # We've made sure person exists and is in this state
            success = TransitionValidationResult(True, None)
            success.add_parameter("name", name)
            yield success

            self.items.pop(known)

        def falling_out(self, item):
            return self.__remove_name(item.name)

        def resolve_differences(self, item):
            return self.__remove_name(item.name)

A state communicates which, after transition validation succeeds, a list of parameters which may be useful to the
next state.

It is also possible to provide a default value in the case where the *-from-* state fails to provide us with a
paramater::

    {"name": TransitionParameter("name"), "foo": TransitionParamater("foo", value="Default Foo")}


State Actions
-------------

Sometimes we want to perform some action on the items tracked in a state. Since these can be quite varied,
state actions are fairly free to do what they like.

Like transitions, we must register them with the TSM and create methods with corresponding names on the state::

    tsm = TrackingStateMachine()

    tsm.add_state(FriendshipState("Friend"))
    tsm.add_state(FriendshipState("Enemy"))

    tsm.add_action("upper_case", "Friend")

And the action definition::

    class FriendshipState(TrackingState):
        def upper_case(self, args):
            initial = args.get("initial", None)

            if not initial:
                raise TransitionActionError("Must provide the intial of the person to upper case")

            for person in self.items:
                if person.name.upper().startswith(initial.upper()):
                    person.name = person.name.upper()

To issue the action we simply::

    tsm.action("upper_case", {"initial": 'J'})

Note, that this action, although technically defined on the ``Enemy`` state, isn't registered with the TSM because
when we registered the action, we specified that the action was on the ``Friend`` state.

Querying States
---------------

``TrackingState`` provides a ``get`` method, we can make use of it and are free to scope its functionality as we
please::

    class Friend(TrackingState):
        def _get(self, initial=None):
            """Return all known persons with the given initial, otherwise return all persons"""

            matches = []
            for person in self.items:
                if not initial:
                    matches.append(person)
                elif person.name.upper().startswith(initial.upper()):
                    matches.append(person)

            # A bit contrived, but shows all our possible return forms
            if not matches:
                return None
            elif len(matches) == 1:
                return matches[0]
            else:
                return mactches

When implementing ``_get`` (note the underscore), you are free to return either:

* ``None`` -- if your criteria matched nothing
* An instance of ``TrackingItem``
* A list of ``TrackingItem``

Items retrieved using ``get`` are always exported as dicts::

    > tsm.state("Friend").get(initial='J')
    {"name": "Jonathan", "reason": "I love myself"}

    > tsm.state("Friend").get(initial='Z')
    None

    > tsm.state("Friend").get()
    [{"name": "Jonathan", "reason": "I love myself"}, {...}, {...}, etc ]