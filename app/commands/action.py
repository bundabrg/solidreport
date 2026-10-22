import click

from actions import ACTIONS
from models.config import Config


@click.command("action")
@click.argument("action")
@click.option(
    "--var",
    help="Pass a variable to actions. Format of 'key=value'. Can be passed multiple times",
    multiple=True,
)
@click.pass_context
def cmd(ctx, action, var):
    """
    Execute the action group
    """

    cfg: Config = ctx.obj["config"]

    variables = {}
    for k, v in [vv.split("=", 1) for vv in var]:
        if k not in variables:
            variables[k] = v
        else:
            if not isinstance(variables[k], list):
                variables[k] = [variables[k]]

            variables[k].append(v)

    # Make sure we have an action group
    if action not in cfg.actions:
        print(f"Can't find action group '{action}' in config file")
        ctx.exit(1)

    print(f"Executing action group '{action}'")

    # For each step in the group, load the action and execute it
    for step in cfg.actions.get(action):
        if step.action not in ACTIONS:
            print(f"  - Unable to find an action called '{step.action}'")
            ctx.exit(1)

        action_def = ACTIONS.get(step.action)
        action_cfg = action_def["model"](**step.model_dump())

        print(f"  - Executing step: {step.description}")
        action_def["execute"](cfg, action_cfg, variables)
