#!/usr/bin/env python2.7

"""
Wei Luo (wl2671), Yuanchu Dang (yd2466)
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, jsonify
import pandas as pd 

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

@app.route('/query_friends')
def query_friends():
	friends_cmd = 'select uid_from, uid_to from friends_with limit 10000;'
	edge = g.conn.execute(text(friends_cmd)).fetchall()
	edge_df = pd.DataFrame(edge)
	edge_df.columns = ['source', 'target']

	all_nodes = list(set(list(edge_df.source) + list(edge_df.target)))
	node_to_int = {key: value for (key, value) in zip(all_nodes, range(len(all_nodes)))}

	node_df = pd.DataFrame([str(node_to_int[n]) for n in all_nodes])
	node_df.columns = ['ID']
	node_df.to_csv('static/node.csv', index = False, header = True)

	edge_df['source'] = edge_df['source'].apply(lambda x: str(node_to_int[x]))
	edge_df['target'] = edge_df['target'].apply(lambda x: str(node_to_int[x]))
	
	edge_df.to_csv('static/edge.csv', index = False, header = True)
	
	# Run the trimming script
	import trim2
	# return jsonify(context)
	return render_template("q3_1.html")
	# import pdb; pdb.set_trace()

@app.route('/query_business', methods=['GET'])
def query_business():
  bid = request.args.get('bid')

  review_cmd = '\
  WITH worst_review AS (\
    SELECT * FROM\
    review_made\
    WHERE bid=(:bid) AND LENGTH(review_text) < 1000\
    ORDER BY stars LIMIT 1\
  )\
  SELECT name, review_text FROM\
  yelp_user INNER JOIN worst_review\
  ON yelp_user.uid = worst_review.uid;\
  '
  review_cursor = g.conn.execute(text(review_cmd), bid=bid)

  review_results = []
  for result in review_cursor:
    review_results.append(result)

  business_cmd = 'SELECT name FROM business WHERE bid=(:bid)'
  business_cursor =  g.conn.execute(text(business_cmd), bid=bid)
  business_results = business_cursor.fetchall()
  
  address_cmd = '\
  SELECT Address.city, Address.state, Address.zipcode\
  FROM Located_At INNER JOIN Address\
  ON Located_At.city = Address.city\
  AND Located_At.state = Address.state\
  AND Located_At.zipcode = Address.zipcode\
  WHERE bid=(:bid)'
  address_cursor = g.conn.execute(text(address_cmd), bid=bid)
  address_results = address_cursor.fetchall()

  hours_cmd = "\
  SELECT Hours.weekday,\
  to_char(Hours.open_time, 'HH12:MI AM') AS open_time,\
  to_char(Hours.close_time, 'HH12:MI AM') AS close_time\
  FROM Open_At INNER JOIN Hours\
  ON Open_At.open_hour=Hours.open_time AND\
  Open_At.close_hour=Hours.close_time AND\
  Open_At.weekday=Hours.weekday\
  WHERE bid=(:bid)\
  ORDER BY\
    CASE\
      WHEN Hours.weekday = 'Sunday' THEN 0\
      WHEN Hours.weekday = 'Monday' THEN 1\
      WHEN Hours.weekday = 'Tuesday' THEN 2\
      WHEN Hours.weekday = 'Wednesday' THEN 3\
      WHEN Hours.weekday = 'Thursday' THEN 4\
      WHEN Hours.weekday = 'Friday' THEN 5\
      WHEN Hours.weekday = 'Saturday' THEN 6\
    END;"
  hours_cursor = g.conn.execute(text(hours_cmd), bid=bid)
  hours_results = hours_cursor.fetchall()

  
  context = dict(review_data = review_results,
                 business_data = business_results,
                 address_data = address_results,
                 hours_data = hours_results)

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
  FROM (tmp INNER JOIN obtain\
  ON tmp.bid = obtain.bid)\
  INNER JOIN checkin\
  ON obtain.weekday = checkin.weekday\
  AND obtain.hour = checkin.hour\
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
