from ModelRecommend import ModelRecommend
from RehabApp import app
import StringIO
from flask import render_template, request, send_file
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

#from bokeh.io import show
from bokeh import embed
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    LinearColorMapper
)
from bokeh.palettes import RdBu9 as palette
from bokeh.plotting import figure, output_notebook, show

from bokeh.sampledata.us_counties import data as countydata

@app.route('/')
@app.route('/home')
def get_model_input():
    plot, rates = map()
    script, div = embed.components(plot)

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
        filled=all, paramdict=paramdict, rec=rec, script=script, div=div, rates=rates)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/index')
def index():
    return render_template("index.html")

def fix_word(word):
    new_word = word.lower().replace('.', '')
    new_word = new_word.replace('saint','st')
    return new_word

def map():
    user = 'gkafka' #add your username here (same as previous postgreSQL)
    host = 'localhost'
    dbname = 'rehab_db'

    db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
    con = None
    con = psycopg2.connect(database = dbname, user = user)
    
    counties = {
        code: county for code, county in countydata.items() if (county["state"] != "ak" and county['state'] != "hi")
        #if county['state'] == 'tx'
    }

    county_xs = [county["lons"] for county in counties.values()]
    county_ys = [county["lats"] for county in counties.values()]
    county_names = [county['name'] for county in counties.values()]

    sql_query = """
                SELECT county, st, pred_diff FROM rehab_table WHERE year=2014;
                """
    df = pd.read_sql_query(sql_query,con)
    
    county_rates = []
    for county in counties.values():
        mask = ((df['county'] == fix_word(county['name'])) &
                (df['st']     == county['state'].upper()))
        if np.sum(mask) == 0:
            county_rates.append(0)
        else:
            county_rates.append(df[mask]['pred_diff'].values[0])

    color_mapper = LinearColorMapper(palette=palette)
    
    source = ColumnDataSource(data=dict(
        x=county_xs,
        y=county_ys,
        name=county_names,
        rate=county_rates,
    ))

    TOOLS = "pan,box_zoom,reset,hover,save"

    p = figure(
        title="Rehab Facility Targets, US Counties", tools=TOOLS,
        x_axis_location=None, y_axis_location=None
    )
    p.grid.grid_line_color = None

    p.patches('x', 'y', source=source,
              fill_color={'field': 'rate', 'transform': color_mapper},
              fill_alpha=0.7, line_color="white", line_width=0.5)

    hover = p.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [
        ("County", "@name"),
        ("True - Predicted Rate", "@rate"),
        ("(Long, Lat)", "($x, $y)"),
    ]

    return p, county_rates
