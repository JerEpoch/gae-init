
from wtforms import Form, validators, StringField,TextAreaField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from google.appengine.api import memcache, urlfetch
import wtforms
import flask
import auth
import model
import util

import requests
import urllib2

from flask import json, request


from blog.routes import blog
from main import app

from config import TMDB_API_KEY

# TO DO
# Get shows suggestions based on current show
# Add a comment system for users
# check out moment js for dates

# https://pythonhosted.org/Flask-Caching/
# https://www.themoviedb.org/documentation/api
# 63639

#flask.request.referer
# request.args
# http://flask.pocoo.org/snippets/63/

class SearchShowForm(FlaskForm):
	name = wtforms.StringField('',validators=[DataRequired(), Length(1,100)])

class NewComment(FlaskForm):
	body = TextAreaField('', validators=[DataRequired(), Length(5, 1500)])


def getAirsToday():
	data = memcache.get('dailyTV')
	
	
	url = "https://api.themoviedb.org/3/tv/airing_today?page=1&language=en-US&api_key=" + TMDB_API_KEY
	if data is not None:
		return data
	else:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			
			if len(data['results']) > 0:
				memcache.add('dailyTV', data['results'], time=3600)
				return data['results']
			else:
				return None

	# if data is not None:
	# 	return data
	# else:
	# 	try:
	# 		json_obj = urllib2.urlopen(url)
	# 		data = json.load(json_obj)

	# 		memcache.add('dailyTV', data['results'], time=3600)
	# 		return data['results']
			
	# 	except urllib2.URLError:
	# 		logging.exception('Caught exception fetching url')


def getSingleShowInfo(id):
	show = []
	id = str(id)
	
	data = memcache.get(id)
	if data is not None:
		return data
	else:
		try:
				url = 'https://api.themoviedb.org/3/tv/' + id + '?language=en-US&api_key=' + TMDB_API_KEY
				result = urlfetch.fetch(url)
				if result.status_code == 200:
					data = json.loads(result.content)
					if len(data) > 0:
						show.append(data)
						memcache.add(id,show,time=3600)
						return show
					else:
						return None
		except urlfetch.Error:
				logging.exception('Caught exception fetching url')

# used for testing stuff
def getShowTest(id):
	show = []
	id = str(id)
	
	data = memcache.get(id)
	if data is not None:
		return data
	else:
		try:
				url = 'https://api.themoviedb.org/3/tv/' + id + '?language=en-US&api_key=' + TMDB_API_KEY
				result = urlfetch(url)
				if result.status_code == 200:
					data = json.load(result.content)
					if len(data['results']) > 0:
						show.append(data)
						memcache.add(id,show,time=3600)
						return show
					else:
						return None
		except urlfetch.Error:
				logging.exception('Caught exception fetching url')

def getShowDetails(data):
	# get a detail search for the show id and store it
	# put this in a loop to get the details for each show
	allShows = []
	for show in data:
		id = str(show['id'])
		name = show['name']
		url = 'https://api.themoviedb.org/3/tv/' + id + '?language=en-US&api_key=' + TMDB_API_KEY
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			allShows.append(data)		
	return allShows

	

def getAirsWeek():
	data = memcache.get('weeklyTV')
	url = 'https://api.themoviedb.org/3/tv/on_the_air?page=1&language=en-US&api_key=' + TMDB_API_KEY
	if data is not None:
		return data
	else:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			if len(data['results']) > 0:
				memcache.add('weeklyTV', data['results'], time=3600)
				return data['results']
			else:
				return None

def getSearched(search):
	search = search.replace(' ', '%20')
	url = 'https://api.themoviedb.org/3/search/tv?page=1&query=' + search +'&language=en-US&api_key=' + TMDB_API_KEY
	try:
			result = urlfetch.fetch(url)
			if result.status_code == 200:
				data = json.loads(result.content)
				return data['results']
			else:
				return None
	except urlfetch.Error:
			logging.exception('Caught exception fetching url')

def isFavorited(id):
	id = str(id)
	fav_db, fav_cursor = model.tvShows.get_dbs(user_key=auth.current_user_key())
	for shows in fav_db:
		if(shows.showId == id):
			return 'True'
	return 'False'

@app.template_filter('datetime')
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)




#=====================================================
#         routes
#=====================================================

@app.route('/shows/<string:searched>/', methods=['GET','POST'])
def show_search(searched):
	#showsWeek = getAirsWeek()
	show_info = getSearched(searched)
	if show_info:
		details = getShowDetails(show_info)
		return flask.render_template('searched.html',
																html_class='searched',
																details = details,
																)
	else:
		errors = "We could not find the show " + searched + ". Please try searching again."
		return flask.render_template('search_error.html', html_class='search-error', errors=errors)


@app.route('/shows/details/<int:id>/', methods=['GET','POST'])
def show_detail(id):
	form = NewComment()
	shows = getSingleShowInfo(id)
	back_url = request.args.get('back')
	showid=str(id)

	if(auth.current_user_id > 0):
		fav = isFavorited(id)

	comments_db, comment_cursor = model.UserComments.get_dbs(showId=showid,order='-created')

	#tvShow = getSearched(show)
	#shows = getShowDetails(tvShow)
	#shows = 'test test'

	if form.validate_on_submit():
		# flask.flash(auth.current_user_db().name)
		comment_db = model.UserComments(user_key=auth.current_user_key(),showId=showid,body=form.body.data, creator=auth.current_user_db().name)
		if comment_db.put():
			flask.flash("Comment Created", category='success')
			return flask.redirect(flask.url_for('show_detail', id=id))

	return flask.render_template('details.html',
																html_class='show_detail',
																shows = shows,
																back_url = back_url,
																fav = fav,
																form=form,
																comments_db=comments_db,
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

# Display all favorite shows
@app.route("/my_favorites/")
@auth.login_required
def my_favorites():
	fav_db, fav_cursor = model.tvShows.get_dbs(user_key=auth.current_user_key())
	#todayShows = getAirsToday()
	return flask.render_template('favorites.html', 
																html_class='my-favorites',
																show=fav_db,
																back_url = 'my_favorites'
																)
# Add to favorites
@app.route("/favorite/<int:id>")
@auth.login_required
def fav_show(id):
	id = str(id)
	show  = getSingleShowInfo(id)
	if(show[0]['poster_path']):
		showPoster = show[0]['poster_path']

	showName = show[0]['original_name']
	fav_db = model.tvShows(
		user_key=auth.current_user_key(),
		showId=id,
		showName=showName,
		showPoster=showPoster,
		)
	fav_db.put()
	flask.flash("Added to Favorites", category='success')
	return flask.redirect(flask.url_for('show_detail', id=id))

# Remove Favorite
@app.route("/favorite/remove/<int:id>")
@auth.login_required
def remove_favorite(id):
	favorite_db = model.tvShows.get_by_id(id)

	if not favorite_db or favorite_db.user_key != auth.current_user_key():
		flask.abort(404)
	else:
		favorite_db.key.delete()
		flask.flash("Removed from favorites.", category='success')
	return flask.redirect(flask.url_for('my_favorites'))

@app.route('/shows_today/', methods=['GET', 'POST'])
def shows_today():
	shows = getAirsToday()
	if shows:
		head = "Shows Airing Today"
		return flask.render_template('todaysShows.html',
																html_class = 'todays-shows',
																shows = shows,
																head = head,
																back_url = 'shows_today'
																)
	else:
		errors = "Something went wrong fetching the current day's shows. Please try again later."
		return flask.render_template('search_error.html', html_class='search-error', errors=errors)

@app.route('/shows_weekly/', methods=['GET', 'POST'])
def shows_weekly():
	shows = getAirsWeek()
	if shows:
		head = "Shows Airing Within A Week"
		return flask.render_template('todaysShows.html',
																html_class = 'todays-shows',
																shows = shows,
																head = head,
																back_url = 'shows_weekly'
																)
	else:
		errors = "Something went wrong getting the weekly shows. Please try again later."
		return flask.render_template('search_error.html', html_class='search-error', errors=errors)

#error route
# most likely do NOT need. NOTE: DELETE LATER
# @app.route('/tvshow/error/')
# def show_error():
# 	return flask.render_template('search_error.html', html_class='search-error',)

# used for testing purposes
@app.route('/shows/test', methods=['GET','POST'])
def show_info():
	return flask.render_template('testing.html', html_class='blah',)



# @app.route('/comment/<int:showid>/new/', methods=['GET','POST'])
# def new_comment(showid):
# 	form = NewComment()
# 	showid=str(showid)

# 	if form.validate_on_submit():
		
# 		comment_db = model.UserComments(user_key=auth.current_user_key(),showId=showid,body=form.body.data)
# 		if comment_db.put():
# 			flask.flash("Comment Created", category='success')
# 	return flask.render_template('new_comment.html', html_class='new-comment', form=form)

# @app.route('/comment/<int:showid>/show/')
# def show_comments(showid):
# 	showid = str(showid)
# 	comment_db = model.UserComments.query().filter(model.UserComments.showId.IN([showid]))

	

# 	return flask.render_template('comments.html', comment_db=comment_db, html_class='comments')
	
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




# =============================================================
# ===							BLOG routes 																=
# =============================================================

# @app.route('/blog/')
# def main_blog():
# 	blog_db, blog_cursor = model.BlogEntry.get_dbs(order='-created')
# 	return flask.render_template('blog.html', html_class='blog-list', blog_db=blog_db)

# @app.route('/blog/new/', methods=['GET', 'POST'])
# @auth.admin_required
# def new_blog():
# 	form = BlogEntryForm()
	
# 	if form.validate_on_submit(): 
# 		flask.flash("Blog entry, " + form.title.data + ", was created.", category='success')
# 		blogs_db = model.BlogEntry(user_key=auth.current_user_key(),title=form.title.data,body=form.body.data,)
# 		blogs_db.put()
		
# 		return flask.redirect(flask.url_for('main_blog'))

# 	return flask.render_template('newblog.html',
# 												html_class='new-blog',
# 												form = form,)


# @app.route('/blog/<int:blog_id>/')
# def blog_entry(blog_id):
# 	blog_db = model.BlogEntry.get_by_id(blog_id)
# 	if not blog_db:
# 		flask.abort(404)

# 	return flask.render_template('blog_view.html', html_class='blog-view',blog=blog_db)

# @app.route('/blog/<int:blog_id>/edit/', methods=['GET', 'POST'])
# @auth.admin_required
# def edit_blog(blog_id):
# 	blog_db = model.BlogEntry.get_by_id(blog_id)
# 	if not blog_db:
# 		flask.abort(404)
# 	form = BlogEntryForm(obj=blog_db)
# 	if form.validate_on_submit():
# 		form.populate_obj(blog_db)
# 		blog_db.put()
# 		return flask.redirect(flask.url_for('blog_entry', blog_id=blog_db.key.id()))

# 	return flask.render_template('blog_edit.html', html_class='blog-edit',form=form)