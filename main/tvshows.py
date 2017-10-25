# coding: utf-8

from wtforms import Form, validators, StringField,TextAreaField, HiddenField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from google.appengine.api import memcache, urlfetch
from webargs import fields as wf
from webargs.flaskparser import parser
import wtforms
import flask
import auth
import model
import util

import requests
import urllib2
import showFunctions #functions related tv show part.

from flask import json, request, session


from blog.routes import blog
from main import app

from config import TMDB_API_KEY
from faker import Factory

# TO DO
# Get shows suggestions based on current show
# Add a comment system for users
# check out moment js for dates
# flask g threads

# https://pythonhosted.org/Flask-Caching/
# https://www.themoviedb.org/documentation/api
# 63639

#flask.request.referer
# request.args
# http://flask.pocoo.org/snippets/63/
# input-group-addon

# CACHE_TIME = 36000

class SearchShowForm(FlaskForm):
	name = wtforms.StringField('',validators=[DataRequired(), Length(1,100)])
	#searchOptions = wtforms.SelectField('Search For:', choices=[('name','TV Show'), ('name','Actor'), ('name','Movie')], default=1)

class NewComment(FlaskForm):
	body = TextAreaField('', validators=[DataRequired(), Length(5, 1500)])
	mediaType = HiddenField()


@app.template_filter('datetime')
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)




#=====================================================
#         routes
#=====================================================

@app.route('/shows/<string:searched>/', methods=['GET','POST'])
def show_search(searched):
	#showsWeek = getAirsWeek()
	show_info = showFunctions.getSearched(searched)
	
	if show_info:
		#details = getShowDetails(show_info)
		head = "Your Search"
		return flask.render_template('tvShows.html',
														html_class = 'searched',
														shows = show_info,
														head = head,
														)
		# return flask.render_template('searched.html',
		# 														html_class='searched',
		# 														details = details,
		# 														)
	else:
		errors = "We could not find the show " + searched + ". Please try searching again."
		return flask.render_template('search_error.html', html_class='search-error', errors=errors)


@app.route('/shows/details/<int:id>/', methods=['GET','POST'])
#@app.route('/shows/details/<int:id>/<string:media>/', methods=['GET','POST'])
def show_detail(id):
	session.pop('media', None)
	media = request.args.get('media')

	if media is None:
		media = 'tv'
	session['media'] = media
	form = NewComment(mediaType=media)
	shows = showFunctions.getDetails(id, media)
	#shows = getSingleShowInfo(id, media)
	back_url = request.args.get('back')
	showId=str(id)

	if(auth.current_user_id > 0):
		fav = showFunctions.isFavorited(id)

	#args = parser.parse({'-created': wf.Str(missing=None) })

	#fake_data(showid)

	comments_db, comments_cursor = model.UserComments.get_dbs(showId = showId, limit=10, prev_cursor=True)
	# comments_query = model.UserComments.query().order(-model.UserComments.created)
	# comments_db = comments_query.filter(model.UserComments.showId == showid)


	if form.validate_on_submit():
		media = form.mediaType.data

		comment = model.UserComments(user_key=auth.current_user_key(), showId=showId, body=form.body.data, 
																		creator=auth.current_user_db().name)
		if comment.put():

			flask.flash("Comment Created", category='success')
			return flask.redirect(flask.url_for('show_detail', id=id, media=media, order='-created'))

	return flask.render_template('details.html',
																html_class='show_detail',
																shows = shows,
																back_url = back_url,
																fav = fav,
																media = media,
																form=form,
																comments_db=comments_db,
																next_url=util.generate_next_url(comments_cursor['next']),
																prev_url=util.generate_next_url(comments_cursor['prev']),
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
	show  = showFunctions.getSingleShowInfo(id)
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

#@app.route('/daily/<int:page>/', methods=['GET', 'POST'])
@app.route('/daily/', methods=['GET', 'POST'])
def shows_today():
	#shows, totalPages = getAirsToday(page)
	#flask.flash(shows, category='success')
	shows = showFunctions.all_shows_daily()
	#sortShows = sort_list(shows)
	#flask.flash(sortShows)
	if shows:
		head = "Today's Shows"
		return flask.render_template('tvShows.html',
																html_class = 'todays-shows',
																shows = shows,
																head = head,
																media = 'tv',
																back_url = 'shows_today'
																)
	else:
		errors = "Something went wrong fetching the current day's shows. Please try again later."
		return flask.render_template('search_error.html', html_class='search-error', errors=errors)

@app.route('/weekly/', methods=['GET', 'POST'])
def shows_weekly():
	#shows, totalPages = getAirsWeek(page)
	shows = showFunctions.all_shows_weekly()
	if shows:
		head = "Weekly Shows"
		return flask.render_template('tvShows.html',
																html_class = 'todays-shows',
																shows = shows,
																head = head,
																media = 'tv',
																back_url = 'shows_weekly'
																)
	else:
		errors = "Something went wrong getting the weekly shows. Please try again later."
		return flask.render_template('search_error.html', html_class='search-error', errors=errors)

@app.route('/similarShows/<int:id>', methods=['GET', 'POST'])
def similarShows(id):
	shows = showFunctions.getSimiliarShows(id)
	if shows:
		head = "Similar Shows"
		return flask.render_template('tvShows.html', html_class='similar-shows', shows=shows, head = head, back_url='similar')

# used for testing purposes
@app.route('/shows/test/', methods=['GET','POST'])
def show_info():
	list_data = [{'name':'red'}, {'name':'blue'}, {'name':'orange'}]
	#shows = [{u'origin_country': [u'US'], u'poster_path': u'/kwThj8DRX0FB9ACIhggDUoUYcSt.jpg', u'name': u'Big Brother', u'overview': u'Big Brother is a television reality game show based on an originally Dutch TV series of the same name created by producer John de Mol in 1997. The show follows a group of HouseGuests living together 24 hours a day in the "Big Brother" house, isolated from the outside world but under constant surveillance with no privacy for three months. Since its television debut in 2000, Big Brother has run continuously with at least one season of the show airing each year. It is currently the second longest running version in the world to have done so, after the Spanish version. The HouseGuests compete for the chance to win a $500,000 grand prize by avoiding weekly eviction, until the last HouseGuest remains at the end of the season that can claim the $500,000 grand prize. The American series is hosted by television personality Julie Chen. Produced by Allison Grodner and Rich Meehan for Fly On The Wall Entertainment, it currently airs in the United States on CBS and Global.\n\nThe show\'s debut season followed the format of most international editions of the series, in which a group of contestants live together and are voted off each week by the viewers. Following a negative critical and commercial reaction to the first season, the format for future changes was drastically changed. For this new format, a group of contestants, known as "HouseGuests," compete to win the series by voting each other off and being the last HouseGuest remaining. One HouseGuest, known as the Head of Household, must nominate two of their fellow HouseGuests for eviction. The winner of the Power of Veto can remove one of the nominees from the block, forcing the HoH to nominate another HouseGuest. The HouseGuests then vote to evict one of the nominees, and the HouseGuest with the most votes is evicted. When only two HouseGuests remained, the last seven evicted HouseGuests, known as the Jury of Seven, would decide which of them would win the $500,000 prize. Much like the first season, the HouseGuests are still under constant surveillance and are filmed at all times. The September 5, 2013 episode marked the show\'s 500th episode.', u'popularity': 72.880838, u'original_name': u'Big Brother', u'id': 10160, u'vote_average': 4.1, u'vote_count': 80, u'first_air_date': u'2000-07-05', u'original_language': u'en', u'backdrop_path': u'/v5ltIEtD9vvfYCFlfMGv1arTWr3.jpg', u'genre_ids': [10764]}, {u'origin_country': [u'US'], u'poster_path': u'/6Fp49zU7FjsJ4xvvZjCZBiBq9KQ.jpg', u'name': u'Zoo', u'overview': u'Set amidst a wave of violent animal attacks sweeping across the planet, a young renegade scientist is thrust into a race to unlock the mystery behind this pandemic before time runs out for animals and humans alike.', u'popularity': 62.38694, u'original_name': u'Zoo', u'id': 62517, u'vote_average': 5.9, u'vote_count': 124, u'first_air_date': u'2015-06-30', u'original_language': u'en', u'backdrop_path': u'/iiCCD2IEDDNSRSmWYHxw6epMNw5.jpg', u'genre_ids': [18, 10759, 10765]}, {u'origin_country': [u'US'], u'poster_path': u'/tu1UNK5AubGdGco3B2Qy8BjFMvU.jpg', u'name': u'General Hospital', u'overview': u'Families, friends, enemies and lovers experience life-changing events in the large upstate New York city of Port Charles, which has a busy hospital, upscale hotel, cozy diner and dangerous waterfront frequented by the criminal underworld.', u'popularity': 57.376718, u'original_name': u'General Hospital', u'id': 987, u'vote_average': 4.6, u'vote_count': 90, u'first_air_date': u'1963-04-01', u'original_language': u'en', u'backdrop_path': u'/vIDHmF9U0gvQ1Oml9lV1LafHwqb.jpg', u'genre_ids': [80, 18, 10766]}, {u'origin_country': [u'US'], u'poster_path': u'/nouJy2Ba1LMbrTkN1bppnK3G9Do.jpg', u'name': u'The Young and the Restless', u'overview': u'The rivalries, romances, hopes and fears of the residents of the fictional Midwestern metropolis, Genoa City. The lives and loves of a wide variety of characters mingle through the generations, dominated by the Newman, Abbott, Baldwin and Winters families.', u'popularity': 50.651021, u'original_name': u'The Young and the Restless', u'id': 1054, u'vote_average': 5.6, u'vote_count': 19, u'first_air_date': u'1973-08-10', u'original_language': u'en', u'backdrop_path': u'/fMwPsGNZ1zQS20qMjmjRpJx3YqM.jpg', u'genre_ids': [10766]}, {u'origin_country': [u'US'], u'poster_path': u'/7r8AepolaDkK8G6LyzyivkaOA60.jpg', u'name': u'Mountain Men', u'overview': u'Most people enjoy the modern technologies and conveniences of today -- smartphones, tablets, cable and satellite TV among them -- but there are people who choose to live off the grid and in the unspoiled wilderness, where dangers like mudslides, falling trees and bears are all parts of life. "Mountain Men" profiles three such people. Eustace Conway, who has lived at the western edge of the Blue Ridge Mountains in North Carolina for more than 25 years, teaches interns about the old ways of living with nature. Tom Oar needs an entire year to prepare for the seven-month-long winter on Montana\'s Yaak River. In Alaska, Marty Meierotto must gather enough wood to survive, in complete isolation, winters that can have temperatures drop to as low as 60 degrees below zero. It\'s not an easy life but for these mountain men, it\'s life as they know it.', u'popularity': 40.417689, u'original_name': u'Mountain Men', u'id': 60381, u'vote_average': 6.2, u'vote_count': 6, u'first_air_date': u'2012-05-31', u'original_language': u'en', u'backdrop_path': u'/iirIMo6HY1cJnbjskABvtvsz0YG.jpg', u'genre_ids': [10764]}, {u'origin_country': [u'US', u'CA'], u'poster_path': u'/ygFkmE24eUb12zWQNiWb9efjBj9.jpg', u'name': u'Ice Road Truckers', u'overview': u'Take a trip to Yellowknife, Canada to experience one of the most dangerous careers around. In unfathomably cold conditions, truck drivers haul equipment and supplies to miners in the Canadian tundra in the dead of winter on a 350-mile highway of ice.', u'popularity': 37.207304, u'original_name': u'Ice Road Truckers', u'id': 3780, u'vote_average': 4.7, u'vote_count': 12, u'first_air_date': u'2007-06-17', u'original_language': u'en', u'backdrop_path': u'/uRbRavVTO1FqwMSnJjTkS0kn1E5.jpg', u'genre_ids': [10764]}, {u'origin_country': [u'US'], u'poster_path': u'/aQMN0xwSzRanStmfyz7qHP4U7LO.jpg', u'name': u'The Guest Book', u'overview': u'The stories of the vacation home Froggy Cottage and its visitors. While the house and cast of characters living in this small mountain town of Mount Trace remain the same, each episode features a different set of vacationing guests.', u'popularity': 37.153925, u'original_name': u'The Guest Book', u'id': 72544, u'vote_average': 7, u'vote_count': 3, u'first_air_date': u'2017-08-03', u'original_language': u'en', u'backdrop_path': u'/4mM13Lh9lifM1lCz8zsf2QSkKe5.jpg', u'genre_ids': [35]}, {u'origin_country': [u'US'], u'poster_path': u'/2PteThhfkwDipsCavIoYz2ka7hE.jpg', u'name': u'Naked SNCTM', u'overview': u'SNCTM is the most exclusive, high-end erotic club ever. Its wealthy members enjoy black tie masquerades, private dinners, and erotic theater. Get to know SNCTM, its creator and its employees in this eye-opening documentary series.', u'popularity': 36.939909, u'original_name': u'Naked SNCTM', u'id': 73473, u'vote_average': 4, u'vote_count': 1, u'first_air_date': u'2017-08-17', u'original_language': u'en', u'backdrop_path': u'/gu3yLUdf7Mg3DMdAgOspUv36BkU.jpg', u'genre_ids': [99]}]
	return flask.render_template('testing.html', html_class='blah', list_data=list_data)

@app.route('/shows/test/list', methods=['GET', 'POST'])
def test_list():
	select = request.form.get('comp_select')
	search = request.form.get('searchFor')
	if not search == "":
		thing = str(select) + " " + str(search)
		return (thing)
	else:
		return "No input"



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
