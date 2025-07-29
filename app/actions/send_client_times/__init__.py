from . import models, action

ACTION = {
    "name": "send_client_times",
    "model": models.ActionModel,
    "execute": action.execute,
}
