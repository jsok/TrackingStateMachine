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

   class MyItem(TrackingItem):
       def __init__(self, name):
           super(self.__class__, self).__init__()
           self.name = name

Here we define a simple item which does nothing but store a name.


Next we define a state::

    class MyState(TrackingState):
        def __init__(self, name):
            super(self.__class__, self).__init__(name, MyItem)
            self.items = []

        def _track(self, item):
            yield TransitionValidationResult(True, None)
            self.items.append(item)


This is a a trivial state which stores a list of MyItem's which currently exist in it.
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

    class MyItem(TrackingItem):
        def __init__(self, name):
            super(self.__class__, self).__init__()
            self.name = name

            self.validations.extend([
                (lambda item: item.name is not "Jonathan"),
            ])

TrackingItem.validations is a list of lambdas which are applied to the item, if any of them are False, the item is
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

    class MyItem(TrackingItem):
        def __init__(self, name):
            super(self.__class__, self).__init__()
            self.name = name

            self.validations.extend([
                (lambda item: isinstance(item.name, str)),
            ])

    class MyState(TrackingState):
        def __init__(self, name):
            super(self.__class__, self).__init__(name, MyItem)
            self.items = []

        def _track(self, item):
        if "Jonathan" in self.items:
            yield TransitionValidationResult(False, "I already have one Jonathan")

        # I'm happy to accept all other names at this point however
        yield TransitionValidationResult(True, None)
        self.items.append(item)

Here we see the guidelines in practise, an item ensures the name is actually a string, but in and of itself,
it has no capacity to check if there exists another item also called Jonathan.

The invariant (only one Jonathan) is enforced in the transition validation.