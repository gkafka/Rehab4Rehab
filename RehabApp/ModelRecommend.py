import pandas as pd
from sklearn import ensemble
from sklearn.externals import joblib

def ModelRecommend(paramdict, y):
    rf = joblib.load('RehabApp/static/model_rf.pkl')
    #ss = joblib.load('RehabApp/static/scale.pkl')

    df = pd.DataFrame([paramdict])
    #ss.transform(df)
    p = rf.predict(df)
    
    rec = ''
    if y-p[0] < -4:
        rec = 'This county has a mortality rate significantly lower than predicted.\n'
    elif y-p[0] > 4:
        rec = 'PEOPLE ARE DYING TOO MUCH.'
    else:
        rec = 'This county has a mortality rate in line with the prediction.\n'

    return rec, p[0]
