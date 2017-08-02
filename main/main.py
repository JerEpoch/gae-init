# coding: utf-8

import flask
import flask_debugtoolbar

import config
import util
from flask_moment import Moment



class GaeRequest(flask.Request):
  trusted_hosts = config.TRUSTED_HOSTS


app = flask.Flask(__name__)
moment = Moment(app)
app.config.from_object(config)



app.request_class = GaeRequest if config.TRUSTED_HOSTS else flask.Request

app.jinja_env.line_statement_prefix = '#'
app.jinja_env.line_comment_prefix = '##'
app.jinja_env.globals.update(
  check_form_fields=util.check_form_fields,
  is_iterable=util.is_iterable,
  slugify=util.slugify,
  update_query_argument=util.update_query_argument,
)

toolbar = flask_debugtoolbar.DebugToolbarExtension(app)
#import auth
import control
import model
import task
import tvshows

from blog.routes import blog

from api import helpers

api_v1 = helpers.Api(app, prefix='/api/v1')

import api.v1

if config.DEVELOPMENT:
  from werkzeug import debug
  try:
    app.wsgi_app = debug.DebuggedApplication(
      app.wsgi_app, evalex=True, pin_security=False,
    )
  except TypeError:
    app.wsgi_app = debug.DebuggedApplication(app.wsgi_app, evalex=True)
  app.testing = False

app.register_blueprint(blog)



