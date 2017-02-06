from ModelRecommend import ModelRecommend
from RehabApp import app
from flask import render_template, request, send_file
import numpy as np
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

user = 'gkafka'
host = 'localhost'
dbname = 'rehab_db'

@app.route('/')
@app.route('/home')
def get_model_input():
    paramdict = {}
    all = True
    rec = ''
    fips = ''
    county = ''
    state = ''
    db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
    con = None
    con = psycopg2.connect(database = dbname, user = user)
    
    sql_query = """
                SELECT st, state, fips_state
                FROM rehab_table
                GROUP BY st, state, fips_state;
                """
    df = pd.read_sql_query(sql_query,con)

    states = []
    for i, row in df.iterrows ():
        states.append ([row['fips_state'], row['state']])

    sql_query = """
                SELECT county, st, state, fips_state, fips
                FROM rehab_table
                GROUP BY county, st, state, fips_state, fips;
                """
    df = pd.read_sql_query(sql_query,con)
    df.sort_values(by=['state', 'county'], inplace=True)

    counties = []
    for i, row in df.iterrows ():
        counties.append([row['fips_state'], row['fips'], ' '.join(w.title() for w in row['county'].split(' '))])
    
    temp = request.args.get('county')
    try:
        if(temp.isdigit()):
            fips = temp
    except:
        pass

    if (fips != ''):
        sql_query = """
                    SELECT n_facilities, opioid_claims, opioid_prescribing_rate,
                           part_d_prescribers, population,
                           death_rate_category_median, pred_diff,
                           county, state
                    FROM rehab_table
                    WHERE fips='{0}' AND year=2014;
                    """.format(fips)
        df = pd.read_sql_query(sql_query,con)
        if df.shape[0] > 0:
            county = ' '.join(w.title() for w in df['county'].values[0].split(' '))
            state = df['state'].values[0]
            paramdict['n_facilities'] = df['n_facilities'].values[0]
            paramdict['Opioid Claims'] = df['opioid_claims'].values[0]
            paramdict['Opioid Prescribing Rate'] = df['opioid_prescribing_rate'].values[0]
            paramdict['Part D Prescribers'] = df['part_d_prescribers'].values[0]
            paramdict['Population'] = df['population'].values[0]

            y = df['death_rate_category_median'].values[0]
            rec, pred = ModelRecommend(paramdict, y)
            paramdict['True y'] = y
            paramdict['Pred y'] = y - df['pred_diff'].values[0]
    
    if len(paramdict) != 7:
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
    
        if all:
            #paramdict['Overall Claims'] = 100.*(paramdict['Opioid Claims'] /
            #                                    paramdict['Opioid Prescribing Rate'])
            rec, pred = ModelRecommend(paramdict, y)
            paramdict['True y'] = y
            paramdict['Pred y'] = pred

    return render_template("home_map.html",
        counties=counties, states=states,
        county=county, state=state,
        paramdict=paramdict, rec=rec, filled=all)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/index')
def index():
    return render_template("index.html")