import click

import reports
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

    vars = {}
    for k, v in [vv.split("=") for vv in var]:
        if k not in vars:
            vars[k] = v
        else:
            if not isinstance(vars[k], list):
                vars[k] = [vars[k]]

            vars[k].append(v)

    # Make sure we have an action group
    if action not in cfg.actions:
        print(f"Can't find action group '{action}' in config file")
        return

    print(f"Executing action group '{action}'")

    # For each step in the group, load the action and execute it
    for step in cfg.actions.get(action):
        if step.action not in ACTIONS:
            print(f"  - Unable to find an action called '{step.action}'")
            return

        action_def = ACTIONS.get(step.action)
        action_cfg = action_def["model"](**step.model_dump())

        print(f"  - Executing step: {step.description}")
        action_def["execute"](cfg, action_cfg, vars)
