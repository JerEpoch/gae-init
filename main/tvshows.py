
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
# 63639

class SearchShowForm(FlaskForm):
	name = wtforms.StringField('Name', validators=[DataRequired()])

class WikiEntryUpdate(FlaskForm):
  title = StringField('Title', validators=[DataRequired()])
  body = TextAreaField('Body', validators=[DataRequired()])

class BlogEntryForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	body = TextAreaField('Body', validators=[DataRequired()])

def getAirsToday():
	data = memcache.get('dailyTV')
	url = "https://api.themoviedb.org/3/tv/airing_today?page=1&language=en-US&api_key=3a3628871c75cfc1fa3bcf7b2f9043aa"
	if data is not None:
		return data
	else:
		try:
				json_obj = urllib2.urlopen(url)
				data = json.load(json_obj)
				memcache.add('dailyTV', data['results'], time=3600)
				return data['results']
		except urllib2.URLError:
				logging.exception('Caught exception fetching url')


def getShowTest(data):
	stuff = []
	for show in data:
		id = str(show['id'])
		name = show['name']
		url = 'https://api.themoviedb.org/3/tv/' + id + '?language=en-US&api_key=3a3628871c75cfc1fa3bcf7b2f9043aa'
		json_obj = urllib2.urlopen(url)
		data = json.load(json_obj)
		stuff.append(data)
	return stuff

def getShowDetails(data):
	# get a detail search for the show id and store it
	# put this in a loop to get the details for each show
	allShows = []
	for show in data:
		id = str(show['id'])
		name = show['name']
		url = 'https://api.themoviedb.org/3/tv/' + id + '?language=en-US&api_key=3a3628871c75cfc1fa3bcf7b2f9043aa'
		memData = memcache.get(name)
		if memData is not None:
			return memData
		else:
			try:
					json_obj = urllib2.urlopen(url)
					data = json.load(json_obj)
					allShows.append(data)
			except urllib2.URLError:
					logging.exception('Caught exception fetching url')
	return allShows
	

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

@app.template_filter('datetime')
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)


#=====================================================
#         routes
#=====================================================

@app.route('/shows/<string:searched>/', methods=['GET','POST'])
def show_search(searched):
	#showsWeek = getAirsWeek()
	searched = getSearched(searched)
	details = getShowDetails(searched)
	return flask.render_template('searched.html',
															html_class='searched',
															details = details,
															)


@app.route('/show/details/', methods=['GET','POST'])
def show_detail():
	shows = getShowDetails()
	#shows = 'test test'
	return flask.render_template('details.html',
																html_class='show_detail',
																shows = shows,
																)


@app.route('/shows/test', methods=['GET','POST'])
def show_info():
	# data = memcache.get('dailyTV')
	thing = getSearched('star trek')
	thing2 = getShowDetails(thing)
	num =getShowTest(thing)
	return flask.render_template('details.html',
																html_class='show_info',
																shows = thing2,
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


@app.route('/shows_today/', methods=['GET', 'POST'])
def shows_today():
	shows = getAirsToday()
	head = "Shows Airing Today"
	return flask.render_template('todaysShows.html',
															html_class = 'todays-shows',
															shows = shows,
															head = head,
															)

@app.route('/shows_weekly/', methods=['post'])
def shows_weekly():
	shows = getAirsWeek()
	head = "Shows Airing Within A Week"
	return flask.render_template('todaysShows.html',
															html_class = 'todays-shows',
															shows = shows,
															head = head,
															)


# =============================================================
# ===							BLOG routes 																=
# =============================================================

@app.route('/blog/')
def main_blog():
	blog_db, blog_cursor = model.BlogEntry.get_dbs(order='-created')
	return flask.render_template('blog.html', html_class='blog-list', blog_db=blog_db)

@app.route('/blog/new/', methods=['GET', 'POST'])
@auth.admin_required
def new_blog():
	form = BlogEntryForm()
	
	if form.validate_on_submit(): 
		flask.flash("Blog entry, " + form.title.data + " ,was created.", category='success')
		blogs_db = model.BlogEntry(user_key=auth.current_user_key(),title=form.title.data,body=form.body.data,)
		blogs_db.put()
		
		return flask.redirect(flask.url_for('main_blog'))

	return flask.render_template('newblog.html',
												html_class='new-blog',
												form = form,)


@app.route('/blog/<int:blog_id>/')
def blog_entry(blog_id):
	blog_db = model.BlogEntry.get_by_id(blog_id)
	if not blog_db:
		flask.abort(404)

	return flask.render_template('blog_view.html', html_class='blog-view',blog=blog_db)

@app.route('/blog/<int:blog_id>/edit', methods=['GET', 'POST'])
@auth.admin_required
def edit_blog(blog_id):
	blog_db = model.BlogEntry.get_by_id(blog_id)
	if not blog_db:
		flask.abort(404)
	form = BlogEntryForm(obj=blog_db)

	return flask.render_template('blog_edit.html', html_class='blog-edit',form=form)

# =============================================================
# ===							Additional routes 													=
# =============================================================

@app.route('/colorgame/', methods=['GET','POST'])
def color_game():
	return flask.render_template('colorGame.html', html_class='color-game',)


@app.route('/other_projects/', methods=['GET', 'POST'])
def wiki_site():
	return flask.render_template('projects.html',
															html_class = 'other-projects',)

