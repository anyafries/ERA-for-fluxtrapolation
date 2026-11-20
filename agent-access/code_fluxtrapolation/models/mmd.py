from .coral import MMD as Model
from .mlp import PARAM_SPACE as MLP_SPACE

PARAM_SPACE = {
    **MLP_SPACE,
    'mmd_lambda': ('loguniform', 1e-3, 1e1),
    'bandwidth_mode': ('choice', ['fixed', 'median']),
}
