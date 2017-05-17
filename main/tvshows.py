from wtforms import Form, validators, StringField,TextAreaField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from google.appengine.api import memcache
import wtforms
import flask
import auth
import model
import util

import urllib2

from flask import json

from main import app

# https://pythonhosted.org/Flask-Caching/
# https://www.themoviedb.org/documentation/api

class SearchShowForm(FlaskForm):
	name = wtforms.StringField('Name', validators=[DataRequired()])

class WikiEntryUpdate(FlaskForm):
  title = StringField('Title', validators=[DataRequired()])
  body = TextAreaField('Body', validators=[DataRequired()])



def getAirsToday():
	data = memcache.get('dailyTV')
	url = "https://api.themoviedb.org/3/tv/airing_today?page=1&language=en-US&api_key=3a3628871c75cfc1fa3bcf7b2f9043aa"
	if data is not None:
		return data
	else:
		try:
				json_obj = urllib2.urlopen(url).read()
				data = json.load(json_obj)
				memcache.add('dailyTV', data['results'], time=3600)
				return data['results']
		except urllib2.URLError:
				logging.exception('Caught exception fetching url')
	

def getAirsWeek():
	data = memcache.get('weeklyTV')
	url = 'https://api.themoviedb.org/3/tv/on_the_air?page=1&language=en-US&api_key=3a3628871c75cfc1fa3bcf7b2f9043aa'
	if data is not None:
		return data
	else:
		json_obj = urllib2.urlopen(url)
		data = json.load(json_obj)
		memcache.add('weeklyTV', data['results'], time=3600)
		return data['results']

def getSearched(search):
	search = search.replace(' ', '%20')
	url = 'https://api.themoviedb.org/3/search/tv?page=1&query=' + search +'&language=en-US&api_key=3a3628871c75cfc1fa3bcf7b2f9043aa'
	try:
			json_obj = urllib2.urlopen(url)
			data = json.load(json_obj)
			return data['results']
	except urllib2.URLError:
			logging.exception('Caught exception fetching url')


#=====================================================
#         routes
#=====================================================

@app.route('/shows/<string:searched>', methods=['GET','POST'])
def show_search(searched):
	showsWeek = getAirsWeek()
	searched = getSearched(searched)
	return flask.render_template('searched.html',
															html_class='searched',
															showsWeek = showsWeek,
															searched = searched,
															)


@app.route('/shows/test', methods=['GET','POST'])
def show_info():
	# data = memcache.get('dailyTV')

	return flask.render_template('showInfo.html',
																html_class='show_info',
																)

# route for when a user searches for a show
@app.route('/search_a_show/', methods=['GET','POST'])
def search_a_show():
	form = SearchShowForm()

	if form.validate_on_submit():
		searched = form.name.data
		return flask.redirect(flask.url_for('show_search', searched=searched))
		#return search

	return flask.render_template('showSearch.html',
															html_class = 'show-search',
															form = form,
															)


@app.route('/shows_today', methods=['GET', 'POST'])
def shows_today():
	shows = getAirsToday()

	return flask.render_template('todaysShows.html',
															html_class = 'todays-shows',
															shows = shows,
															)

@app.route('/colorgame/', methods=['GET','POST'])
def color_game():
	return flask.render_template('colorGame.html', html_class='color-game',)


@app.route('/other_projects/', methods=['GET', 'POST'])
def wiki_site():
	return flask.render_template('projects.html',
															html_class = 'other-projects',)

