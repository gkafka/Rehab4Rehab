from ModelRecommend import ModelRecommend
from RehabApp import app
import StringIO
from flask import render_template, request, send_file
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import pandas as pd

#from bokeh.io import show
from bokeh import embed
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    LinearColorMapper
)
from bokeh.palettes import Viridis6 as palette
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

@app.route('/map_basemap')
def map_basemap():
    fig, ax = plt.subplots(figsize=(15,9))

    m = Basemap(resolution='l', # c, l, i, h, f or None
                projection='lcc',
                lat_1=33, lat_2=45, lon_0=-95,
                llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-64, urcrnrlat=49)

    m.readshapefile('RehabApp/static/cb_2015_us_county_5m', 'County')

    df = pd.DataFrame({
            'shapes': [mpl.patches.Polygon(np.array(shape), True) for shape in m.County],
            'area': [county['NAME'] for county in m.County_info]
        })

    cmap = plt.get_cmap('Oranges')
    pc = mpl.collections.PatchCollection(df.shapes, zorder=2)
    norm = mpl.colors.Normalize()

    pc.set_facecolor(cmap(norm(np.random.rand(df.shape[0]))))
    ax.add_collection(pc)
    
    img = StringIO.StringIO()
    fig.savefig(img)
    img.seek(0)
    return send_file(img, mimetype='image/png')

def map():
    palette.reverse()

    counties = {
        code: county for code, county in countydata.items() if (county["state"] != "ak" and county['state'] != "hi")
        #if county['state'] == 'tx'
    }

    county_xs = [county["lons"] for county in counties.values()]
    county_ys = [county["lats"] for county in counties.values()]

    county_names = [county['name'] for county in counties.values()]
    county_rates = np.random.rand(len(counties))
    color_mapper = LinearColorMapper(palette=palette)
    
    source = ColumnDataSource(data=dict(
        x=county_xs,
        y=county_ys,
        name=county_names,
        rate=county_rates,
    ))

    TOOLS = "pan,box_zoom,reset,hover,save"

    p = figure(
        title="Texas Unemployment, 2009", tools=TOOLS,
        x_axis_location=None, y_axis_location=None
    )
    p.grid.grid_line_color = None

    p.patches('x', 'y', source=source,
              fill_color={'field': 'rate', 'transform': color_mapper},
              fill_alpha=0.7, line_color="white", line_width=0.5)

    hover = p.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [
        ("Name", "@name"),
        ("Unemployment rate)", "@rate"),
        ("(Long, Lat)", "($x, $y)"),
    ]

    return p, county_rates
