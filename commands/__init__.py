# Here you define the commands that will be added to your add-in.

# Import the modules corresponding to the commands you created.
# If you want to add an additional command, duplicate one of the existing directories and import it here.
# You need to use aliases (import "entry" as "my_module") assuming you have the default module named "entry".
from .shareDocument import entry as shareDocument
from .shareSettings import entry as shareSettings
from .shareOpenDesktop import entry as shareOpenDesktop

# Fusion will automatically call the start() and stop() functions.
commands = [
    shareDocument,
    shareSettings,
    shareOpenDesktop,
]


# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()


# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()
