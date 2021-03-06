# -*- coding: utf-8 -*-
"""bitcoin prediction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nBFfVJFIBxTyqkBQp7xbeHNMHa6y3n5u
"""

# Commented out IPython magic to ensure Python compatibility.
# pip install pyforest
from pyforest import *
from matplotlib import pyplot as plt
import seaborn as sns
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
import sklearn.metrics
import seaborn as sns
from pylab import rcParams

# %matplotlib inline
pd.set_option("display.max_columns", 500)
pd.set_option("display.max_rows", 500)
# from google.colab import files

plt.style.use("ggplot")

# from keras.models import Sequential
# from keras.layers import Dense, LSTM, Dropout, GRU, Bidirectional
# from keras.optimizers import SGD
import math

# import pandas_datareader as web
import warnings

# Use Cross-validation.
from sklearn.model_selection import cross_val_score

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import (
    LinearDiscriminantAnalysis,
    QuadraticDiscriminantAnalysis,
)
from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn import model_selection
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import KFold
from sklearn.neural_network import MLPClassifier


warnings.filterwarnings("ignore")
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 150)

# pip install yfinance

import yfinance as yf

btc = yf.Ticker("BTC-USD")
# get historical market data
hist = btc.history(period="max")
df = hist[["Open", "High", "Low", "Close", "Volume"]]
df = df.sort_index(ascending=True)
print(df.tail())
print()
print(df.shape)

df.head()

df.describe()

df["Close"].hist(bins=30, figsize=(10, 5)).axvline(
    df["Close"].mean(), color="b", linestyle="dashed", linewidth=2
)
plt.show()

fig = go.Figure(
    data=[
        go.Candlestick(
            x=df.index[-30:],
            open=df["Open"][-30:],
            high=df["High"][-30:],
            low=df["Low"][-30:],
            close=df["Close"][-30:],
        )
    ]
)
fig.update_xaxes(showline=True, linewidth=2, linecolor="black", mirror=True)
fig.update_yaxes(showline=True, linewidth=2, linecolor="black", mirror=True)
fig.update_layout(title="Last 30 days BTC price", yaxis_title="BTC (US$)")
fig.show()

# Create the shifted lag series of prior trading period close values
lags = 2
for i in range(0, lags):
    df["Lag%s" % str(i + 1)] = df["Close"].shift(i + 1).pct_change()

df["Open-Close"] = (df.Open - df.Close).pct_change()
df["High-Low"] = (df.High - df.Low).pct_change()
df["volume_gap"] = df.Volume.pct_change()
df.head()

# Shift -1 for next day's return
df["forward_ret"] = df["Close"].shift(-1) / df["Open"].shift(-1) - 1
# If tomorrow's return > 0, then 1; #If tomorrow's return <= 0, then -1
df["y_clas"] = -1
df.at[df["forward_ret"] > 0.0, "y_clas"] = 1
# Remove it make ensure no look ahead bias
del df["forward_ret"]

# plot target variable
plt.figure(figsize=(8, 4))
sns.countplot("y_clas", data=df)
plt.title("Target Variable Counts")
plt.show()

# pip install tscv

# collect necessary features
data = df[["Close", "Lag1", "Lag2", "Open-Close", "High-Low", "volume_gap", "y_clas"]]
data.dropna(inplace=True)

# create X, y set
X = data.drop(["y_clas", "Close"], 1)
y_clas = data.y_clas

SP = 0.80  # split percentage
split = int(SP * len(data))
print("Split:", split)

# Train data set
xTrain = X[:split]
yTrain = y_clas[:split]
# Test data set
xTest = X[split:]
yTest = y_clas[split:]

print("Observations: %d" % (len(xTrain) + len(xTest)))
print("Training Observations: %d" % (len(xTrain)))
print("Testing Observations: %d" % (len(xTest)))


# prepare configuration for cross validation test harness
seed = 42
# prepare models
models = []
models.append(("XGB", XGBClassifier()))
models.append(("LR", LogisticRegression(solver="lbfgs")))
models.append(("KNN", KNeighborsClassifier()))
models.append(("LDA", LinearDiscriminantAnalysis()))
models.append(
    (
        "RF",
        RandomForestClassifier(
            n_estimators=1000,
            criterion="gini",
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            max_features="auto",
            bootstrap=True,
            oob_score=False,
            n_jobs=1,
            random_state=None,
            verbose=0,
        ),
    )
)
models.append(("QDA", QuadraticDiscriminantAnalysis()))
models.append(("LSVC", LinearSVC()))
models.append(
    (
        "RSVM",
        SVC(
            C=1000000.0,
            cache_size=200,
            class_weight=None,
            coef0=0.0,
            degree=3,
            gamma=0.0001,
            kernel="rbf",
            max_iter=-1,
            probability=False,
            random_state=None,
            shrinking=True,
            tol=0.001,
            verbose=False,
        ),
    )
)

# evaluate each model in turn
results = []
names = []
scoring = "accuracy"
kf = KFold(n_splits=5)
for name, model in models:
    # kfold = model_selection.KFold(n_splits=10, random_state=seed)
    cv_results = model_selection.cross_val_score(
        model, xTrain, yTrain, cv=kf, scoring=scoring
    )
    results.append(cv_results)
    names.append(name)
    msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
    print(msg)
    print()

# iterate over the models
for i in models:
    # Training each of the models on the training set
    i[1].fit(xTrain, yTrain)
    # predictions on the test set
    pred = i[1].predict(xTest)
    # Accuracy Score and the confusion matrix for each model
    print("%s:\n%0.3f" % (i[0], i[1].score(xTest, yTest)))
    print("%s\n" % confusion_matrix(pred, yTest))

rf = RandomForestClassifier(
    n_estimators=1000,
    criterion="gini",
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features="auto",
    bootstrap=True,
    oob_score=False,
    n_jobs=1,
    random_state=None,
    verbose=00,
).fit(xTrain, yTrain)

import itertools

# Evaluation of Model - Confusion Matrix Plot
def plot_confusion_matrix(
    cm, classes, title="Confusion matrix", normalize=False, cmap=plt.cm.Blues
):
    if normalize:
        cm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print("Confusion matrix")
    print(cm)
    plt.imshow(cm, interpolation="nearest", cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = ".2f" if normalize else "d"
    thresh = cm.max() / 2.0
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(
            j,
            i,
            format(cm[i, j], fmt),
            horizontalalignment="center",
            color="white" if cm[i, j] > thresh else "black",
        )

    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()


# make predictions for test data
y_pred = rf.predict(xTest)
# Compute confusion matrix
results = confusion_matrix(yTest, y_pred)

# Plot non-normalized confusion matrix
plt.figure()
plot_confusion_matrix(results, classes=["1", "-1"], title="Confusion matrix")

FP = results.sum(axis=0) - np.diag(results)
FN = results.sum(axis=1) - np.diag(results)
TP = np.diag(results)
TN = results.sum() - (FP + FN + TP)

FP = FP.astype(float)
FN = FN.astype(float)
TP = TP.astype(float)
TN = TN.astype(float)

pd.DataFrame(y_pred).value_counts()

DfTrade = data[["Close"]].copy()
# Dftrade = DfTrade[DfTrade.index > '2020'].copy()
DfTrade["trade_signal"] = rf.predict(X)
# log returns

"""
log returns of today (log of the close price of today) / close price of yesterday.
log-returns are added to show performance across time
"""
DfTrade["simple_ret"] = np.log(DfTrade["Close"] / DfTrade["Close"].shift(1))

"""
the simple_ret values are shifted upwards by one element so that tomorrow’s returns are stored against the prices of today
"""
DfTrade["simple_ret"] = DfTrade["simple_ret"].shift(-1)

# Strategy Returns
DfTrade["startegy_ret"] = DfTrade["simple_ret"] * DfTrade["trade_signal"]
# cumulative returns
DfTrade["cum_ret"] = DfTrade[split:]["simple_ret"].cumsum()
# Cumulative Strategy Returns
DfTrade["startegy_ret"] = DfTrade["simple_ret"] * DfTrade["trade_signal"]
DfTrade["cum_strategy_ret"] = DfTrade[split:]["startegy_ret"].cumsum()

# visualize the performance
plt.style.use("dark_background")
plt.figure(figsize=(15, 5))
plt.plot(DfTrade.cum_ret, color="r", label="BitCoin Simple Returns")
plt.plot(DfTrade.cum_strategy_ret, color="g", label="BitCoin Strategy Returns")
plt.ylabel("Strategy Returns (%)")
plt.legend()
plt.show()

print("Market returns:", round(DfTrade["cum_ret"].sum(), 2))
print("Trading Strategy returns:", round(DfTrade["cum_strategy_ret"].sum(), 2))
