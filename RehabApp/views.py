from ModelRecommend import ModelRecommend
from flask import render_template
from flask import request
from RehabApp import app
import pandas as pd

@app.route('/')
@app.route('/home')
def get_model_input():
    paramdict = {}
    
    all = True
    temp = request.args.get('population')
    try:
        formatted = int(temp)
        paramdict['Population'] = formatted
    except:
        all = False;

    temp = request.args.get('n_facility')
    try:
        formatted = int(temp)
        paramdict['n_facilities'] = formatted
    except:
        all = False;

    temp = request.args.get('opioidclaim')
    try:
        formatted = int(temp)
        paramdict['Opioid Claims'] = formatted
    except:
        all = False;

    temp = request.args.get('opioid_rate')
    try:
        formatted = float(temp)
        paramdict['Opioid Prescribing Rate'] = formatted
    except:
        all = False;

    temp = request.args.get('prescribers')
    try:
        formatted = int(temp)
        paramdict['Part D Prescribers'] = formatted
    except:
        all = False;

    temp = request.args.get('mortality')
    y = -1;
    try:
        y = int(temp)
    except:
        all = False;
    
    rec = ''
    if all:
        paramdict['Overall Claims'] = 100.*(paramdict['Opioid Claims'] /
                                            paramdict['Opioid Prescribing Rate'])
        rec, pred = ModelRecommend(paramdict, y)
        paramdict['True y'] = y
        paramdict['Pred y'] = pred

    return render_template("home_model.html",
        filled=all, paramdict=paramdict, rec=rec)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/index')
def index():
    return render_template("index.html")