from . import models, action

ACTION = {
    "name": "send_staff_times_summary",
    "model": models.ActionModel,
    "execute": action.execute,
}
