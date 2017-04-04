import aria.cli.commands as commands
import click.testing


def invoke(command):
    # TODO handle verbosity later
    command_string = ['service_templates', 'show', '1']
    command, sub, args = command_string[0], command_string[1], command_string[2:]
    runner = click.testing.CliRunner()
    outcome = runner.invoke(getattr(
        getattr(commands, command), sub), args)
    return outcome