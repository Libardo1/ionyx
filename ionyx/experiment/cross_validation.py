import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cross_validation import KFold
from sklearn.learning_curve import learning_curve

from ..utils import fit_transforms, apply_transforms, score


def cross_validate(X, y, model, metric, transforms, n_folds):
    """
    Performs cross-validation to estimate the true performance of the model.
    """
    t0 = time.time()
    y_train_scores = []
    y_pred = np.array([])
    y_true = np.array([])

    folds = list(KFold(y.shape[0], n_folds=n_folds, shuffle=True, random_state=1337))
    for i, (train_index, eval_index) in enumerate(folds):
        print('Starting fold {0}...'.format(i + 1))
        X_train = X[train_index]
        y_train = y[train_index]
        X_eval = X[eval_index]
        y_eval = y[eval_index]

        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)

        model.fit(X_train, y_train)

        y_train_scores.append(score(y_train, model.predict(X_train), metric))
        y_pred = np.append(y_pred, model.predict(X_eval))
        y_true = np.append(y_true, y_eval)

    t1 = time.time()
    print('Cross-validation completed in {0:3f} s.'.format(t1 - t0))

    print('Average training score = '), sum(y_train_scores) / len(y_train_scores)

    cross_validation_score = score(y_true, y_pred, metric)
    print('Cross-validation score = '), cross_validation_score

    return cross_validation_score


def sequence_cross_validate(X, y, model, metric, transforms, n_folds, strategy='traditional',
                            window_type='cumulative', min_window=0, forecast_range=1, plot=False):
    """
    Performs time series cross-validation to estimate the true performance of the model.
    """
    scores = []
    train_count = len(X)

    if strategy == 'walk-forward':
        n_folds = train_count - min_window - forecast_range
        fold_size = 1
    else:
        fold_size = train_count / n_folds

    t0 = time.time()
    for i in range(n_folds):
        if window_type == 'fixed':
            fold_start = i * fold_size
        else:
            fold_start = 0

        fold_end = (i + 1) * fold_size + min_window
        fold_train_end = fold_end - forecast_range

        X_train, X_eval = X[fold_start:fold_train_end, :], X[fold_train_end:fold_end, :]
        y_train, y_eval = y[fold_start:fold_train_end], y[fold_train_end:fold_end]

        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_eval)
        scores.append(score(y, y_pred, metric))

        if plot is True:
            fig, ax = plt.subplots(figsize=(16, 10))
            ax.set_title('Estimation Error')
            ax.plot(y_pred - y_eval)
            fig.tight_layout()

    t1 = time.time()
    print('Cross-validation completed in {0:3f} s.'.format(t1 - t0))

    return np.mean(scores)


def plot_learning_curve(X, y, model, metric, transforms, n_folds):
    """
    Plots a learning curve showing model performance against both training and
    validation data sets as a function of the number of training samples.
    """
    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)

    t0 = time.time()
    train_sizes, train_scores, test_scores = learning_curve(model, X, y, scoring=metric, cv=n_folds, n_jobs=1)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_title('Learning Curve')
    ax.set_xlabel('Training Examples')
    ax.set_ylabel('Score')
    ax.fill_between(train_sizes, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std,
                    alpha=0.1, color='b')
    ax.fill_between(train_sizes, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std,
                    alpha=0.1, color='r')
    ax.plot(train_sizes, train_scores_mean, 'o-', color='b', label='Training score')
    ax.plot(train_sizes, test_scores_mean, 'o-', color='r', label='Cross-validation score')
    ax.legend(loc='best')
    fig.tight_layout()
    t1 = time.time()
    print('Learning curve generated in {0:3f} s.'.format(t1 - t0))
