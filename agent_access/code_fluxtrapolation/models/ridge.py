from sklearn.linear_model import Ridge


class Model(Ridge):
    standardize = True


PARAM_SPACE = {'alpha': ('loguniform', 1e-3, 1e2)}
