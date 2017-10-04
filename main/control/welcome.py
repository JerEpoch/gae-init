# coding: utf-8

import flask
import model
import config

from main import app



###############################################################################
# Welcome
###############################################################################
@app.route('/')
def welcome():
	blog_db, blog_cursor = model.BlogEntry.get_dbs(limit=2, order='-created')
	return flask.render_template('welcome.html', html_class='welcome', blog_db=blog_db)


###############################################################################
# Sitemap stuff
###############################################################################
@app.route('/sitemap.xml')
def sitemap():
  response = flask.make_response(flask.render_template(
    'sitemap.xml',
    lastmod=config.CURRENT_VERSION_DATE.strftime('%Y-%m-%d'),
  ))
  response.headers['Content-Type'] = 'application/xml'
  return response


###############################################################################
# Warmup request
###############################################################################
@app.route('/_ah/warmup')
def warmup():
  # TODO: put your warmup code here
  return 'success'
