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

Transitions and Tracking
------------------------

As just mentioned, transitions and item tracking are implemented using generators.
TrackingState implementations need to conform to this protocol by:

1. Performing ``yield TransitionValidationResult(True, None)`` to tell TSM that they are ready to commit to the
   transition.

2. If they decide that a transition will break one of their invariants, they can perform:
   ``yield TransitionValidationResult(False, "DO NOT WANT!")``
   to tell TSM that the transition should abort.
