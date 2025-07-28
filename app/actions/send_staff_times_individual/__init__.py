from . import models, action

ACTION = {
    "name": "send_staff_times_individual",
    "model": models.ActionModel,
    "execute": action.execute,
}
