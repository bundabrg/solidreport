import click

import reports


@click.group('generate')
def cmd():
    pass

# Add all report generate commands
for c in reports.GENERATE:
    cmd.add_command(c)