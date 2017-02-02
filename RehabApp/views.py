from ModelRecommend import ModelRecommend
from RehabApp import app
from flask import render_template, request, send_file
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

user = 'gkafka'
host = 'localhost'
dbname = 'rehab_db'

@app.route('/')
@app.route('/home')
def get_model_input():
    plot = map()
    script, div = embed.components(plot)

    db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
    con = None
    con = psycopg2.connect(database = dbname, user = user)
    
    sql_query = """
                SELECT county, st, state FROM rehab_table GROUP BY county, st, state;
                """
    df = pd.read_sql_query(sql_query,con)
    df.sort_values(by=['state', 'county'], inplace=True)

    menu_entries = []
    for i in xrange(df.shape[0]):
        menu_entries.append("{0}, {1}".format(df.iloc[i]['st'], df.iloc[i]['county'].upper()))

    return render_template("home_map.html",
        script=script, div=div, menu_entries=menu_entries)

@app.route('/explorer')
def explore():
    paramdict = {}
    all = True
    rec = ''

    db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
    con = None
    con = psycopg2.connect(database = dbname, user = user)
    
    sql_query = """
                SELECT county, st, state FROM rehab_table GROUP BY county, st, state;
                """
    df = pd.read_sql_query(sql_query,con)
    df.sort_values(by=['state', 'county'], inplace=True)

    menu_entries = []
    for i in xrange(df.shape[0]):
        menu_entries.append("{0}, {1}".format(df.iloc[i]['st'], df.iloc[i]['county'].upper()))
    
    county = ''
    state = ''
    temp = request.args.get('countyst')
    try:
        wordlist = temp.split(', ')
        state = wordlist[0]
        county = wordlist[1].lower()
    except:
        pass

    if (county != '') and (state != ''):
        sql_query = """
                    SELECT n_facilities, opioid_claims, opioid_prescribing_rate,
                           part_d_prescribers, population,
                           death_rate_category_median, pred_diff
                    FROM rehab_table
                    WHERE county='{0}' AND st='{1}';
                    """.format(county, state)
        df = pd.read_sql_query(sql_query,con)
        if df.shape[0] > 0:
            county = ' '.join(w.title() for w in county.split(' '))
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

    return render_template("explorer.html",
        menu_entries=menu_entries,
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

def fix_word(word):
    new_word = word.lower().replace('.', '')
    new_word = new_word.replace('saint','st')
    return new_word

def map():
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

    return p
