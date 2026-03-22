import os

import sims4.commands
from server_commands.argument_helpers import OptionalTargetParam
from sims4.reload import reload_file

__version__ = "1.0.0"


@sims4.commands.Command("s4f.reload", command_type=sims4.commands.CommandType.Live)
def reload(module: str, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        dirname = os.path.dirname(os.path.realpath(__file__))
        for filename in os.listdir(dirname):
            try:
                if filename.endswith(".py") and filename[:-3] != "__init__":
                    output("Reloading {}".format(filename))
                    reloaded_module = reload_file(os.path.join(dirname, filename))
                    if reloaded_module is not None:
                        output(f"Done reloading - {filename}")
                    else:
                        output("Error loading module or module does not exist")
            except BaseException as e:
                output("Reload failed: ")
                for v in e.args:
                    output(v)
    except BaseException as e:
        output("Reload failed: ")
        for v in e.args:
            output(v)


@sims4.commands.Command("s4f.version", command_type=sims4.commands.CommandType.Live)
def version(
    opt_sim: OptionalTargetParam = None,  # pyright: ignore[reportArgumentType]
    _connection=None,
):
    output = sims4.commands.CheatOutput(_connection)
    output(__version__)
    return True
