from distutils.core import setup

setup(
    name='TrackingStateMachine',
    version='0.1.0',
    author='Jonathan Sokolowski',
    author_email='jonathan.sokolowski@gmail.com',
    packages=['tracking_state_machine', 'tracking_state_machine.test'],
    url='http://pypi.python.org/pypi/TrackingStateMachine/',
    license='LICENSE',
    description='State machine which can simultaneously track items in all states and manage transitions.',
    long_description="A State Machine which can simultaneously track many items in all states and manage transitions.",
    install_requires=[],
)
