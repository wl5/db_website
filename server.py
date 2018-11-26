#!/usr/bin/env python2.7

"""
Wei Luo (wl2671), Yuanchu Dang (yd2466)
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates/')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "wl2671"
DB_PASSWORD = "s67cr9rz"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


# create engine
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  Setup a database connection that can be used throughout the request
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  Close the database connection.
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  # DEBUG: this is debugging code to see what request looks like
  print request.args

  #context = dict(data = names)

  return render_template("index.html")

@app.route('/query_business', methods=['GET'])
def query_business():
  bid = request.args.get('bid')

  cmd = '\
  WITH worst_review AS (\
    SELECT * FROM\
    review_made WHERE bid=(:bid) ORDER BY stars LIMIT 1\
  )\
  SELECT name, review_text FROM\
  yelp_user INNER JOIN worst_review\
  ON yelp_user.uid = worst_review.uid;\
  '
  cursor = g.conn.execute(text(cmd), bid=bid);

  results = []
  for result in cursor:
    print(result)
    results.append(result)

  context = dict(bid_data = results)

  return render_template("details.html", **context)

  

@app.route('/query_by_star', methods=['GET'])
def query_by_star():
  zipcode = request.args.get('zipcode')
  
  cmd = '\
  WITH tmp(bid, name) AS (\
    SELECT business.bid, name FROM\
      located_at INNER JOIN business \
      ON located_at.bid = business.bid \
    WHERE zipcode=(:zipcode)\
  ) \
  SELECT ROUND(AVG(review_made.stars),0) AS avg_stars,\
  tmp.name,\
  tmp.bid\
  FROM tmp INNER JOIN review_made\
  ON tmp.bid = review_made.bid\
  GROUP BY tmp.bid, tmp.name\
  ORDER BY avg_stars\
  LIMIT 4;';
  cursor = g.conn.execute(text(cmd), zipcode = zipcode);

  results = []
  for result in cursor:
    results.append(result)

  context = dict(data = results, section = "portfolio")
    
  return render_template("index.html", **context)

@app.route('/query_by_checkin', methods=['GET'])
def query_by_checkin():
  zipcode = request.args.get('zipcode')
  
  cmd = 'WITH tmp(bid, name) AS (\
    SELECT business.bid, name FROM\
      located_at INNER JOIN business\
    ON located_at.bid = business.bid\
    WHERE zipcode=(zipcode)\
  )\
  SELECT SUM(obtain.count) AS total_checkins,\
  tmp.name,\
  tmp.bid\
  FROM tmp INNER JOIN obtain\
  ON tmp.bid = obtain.bid\
  GROUP BY tmp.bid, tmp.name\
  ORDER BY total_checkins\
  LIMIT 4;'
  
  cursor = g.conn.execute(text(cmd), zipcode = zipcode);

  results = []
  for result in cursor:
    results.append(result)

  context = dict(data2 = results, section = "portfolio")
    
  return render_template("index.html", **context)



if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
