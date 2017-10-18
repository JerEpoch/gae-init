
from google.appengine.api import memcache, urlfetch
import auth
import model
from flask import json, request
from config import TMDB_API_KEY

CACHE_TIME = 36000

# class SearchShowForm(FlaskForm):
# 	name = wtforms.StringField('',validators=[DataRequired(), Length(1,100)])
# 	#searchOptions = wtforms.SelectField('Search For:', choices=[('name','TV Show'), ('name','Actor'), ('name','Movie')], default=1)

# class NewComment(FlaskForm):
# 	body = TextAreaField('', validators=[DataRequired(), Length(5, 1500)])

# def fake_data(id):
# 	fake = Factory.create()
# 	for _ in range(30):
# 		name = fake.name()
# 		body = fake.text()
# 		#body = "Suspendisse gravida lorem vitae velit feugiat, id pulvinar magna euismod. Integer vel euismod turpis. Vestibulum tempor vehicula justo, et tristique erat dictum ut. Ut vel sem faucibus, placerat velit tristique, rutrum enim. Quisque rhoncus neque nec tortor faucibus maximus. Sed congue mi sed libero sagittis, ut convallis nisi auctor. Aliquam consequat dolor nec elementum pellentesque. Donec viverra felis nunc, non dapibus odio euismod vel. Nam in quam eget ante convallis efficitur ut vel lorem."
# 		comment_db = model.UserComments(user_key=auth.current_user_key(), showId=id, body=body, 
# 																		creator=name)
# 		comment_db.put()


def getAirsToday(page):
	page = str(page)
	
	# gets memcache of shows airing today on the current user page
	data = memcache.get('dailyTV' + page)

	
	url = "https://api.themoviedb.org/3/tv/airing_today?page=" + page + "&language=en-US&api_key=" + TMDB_API_KEY

	#if there is data in memcache, just return that. else it will grab it from TMDB api
	if data is not None:
		return data['results'], data['total_pages']
	else:
		result = urlfetch.fetch(url)
		# if the fetch was ok, then convert the json to a dictionary
		if result.status_code == 200:
			data = json.loads(result.content)
			# just a check to ensure there is data, then adds it to the memcache and returns it.
			if len(data['results']) > 0:
				memcache.add('dailyTV' + page, data, time=CACHE_TIME)
				memcache.add('dailyTV', data, time=CACHE_TIME)
				return data['results'], data['total_pages']
			else:
				return None

def all_shows_daily():
	# gets all the shows for the day, puts them in a list and then sends them to be sorted by US country and returns that
	totalShows = []
	shows = []
	page = '1'
	url = "https://api.themoviedb.org/3/tv/airing_today?page=" + page + "&language=en-US&api_key=" + TMDB_API_KEY
	data = memcache.get('dailyUS')

	if data is not None:
		return data
	else:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			if data['total_pages'] > 1:
				for page in range(1, data['total_pages'] + 1):
					page = str(page)
					url = "https://api.themoviedb.org/3/tv/airing_today?page=" + page + "&language=en-US&api_key=" + TMDB_API_KEY
					result = urlfetch.fetch(url)
					data = json.loads(result.content)
					shows = data['results']
					for show in shows:
						totalShows.append(show)

		sort_shows = sort_list(totalShows)
		memcache.add('dailyUS', sort_shows, time=CACHE_TIME)

	return sort_shows

def all_shows_weekly():
	totalShows = []
	shows = []
	page = '1'
	url = "https://api.themoviedb.org/3/tv/on_the_air?page=" + page +"&language=en-US&api_key=" + TMDB_API_KEY
	data = memcache.get('weeklyUS')

	if data is not None:
		return data
	else:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			if data['total_pages'] > 1:
				for page in range(1, data['total_pages'] + 1):
					page = str(page)
					url = "https://api.themoviedb.org/3/tv/on_the_air?page=" + page +"&language=en-US&api_key=" + TMDB_API_KEY
					result = urlfetch.fetch(url)
					data = json.loads(result.content)
					shows = data['results']
					for show in shows:
						totalShows.append(show)

		sort_shows = sort_list(totalShows)
		memcache.add('weeklyUS', sort_shows, time=CACHE_TIME)
		return sort_shows


def getSimiliarShows(id):
	id = str(id)
	totalShows = []
	shows = []
	page = '1'
	url = "https://api.themoviedb.org/3/tv/" + id + "/similar?api_key="+ TMDB_API_KEY + "&language=en-US&page=" + page
	data = memcache.get('similarShows' + id)

	if data is not None:
		return data
	else:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			if data['total_pages'] > 1:
				for page in range(1, data['total_pages'] + 1):
					page = str(page)
					url = "https://api.themoviedb.org/3/tv/" + id + "/similar?api_key="+ TMDB_API_KEY + "&language=en-US&page=" + page
					result = urlfetch.fetch(url)
					data = json.loads(result.content)
					shows = data['results']
					for show in shows:
						totalShows.append(show)

		sort_shows = sort_list(totalShows)
		memcache.add('similarShows' + id, sort_shows, time=CACHE_TIME)
		return sort_shows
	

def sort_list(shows):
	# returns a list with US only shows.
	# showTime for either daily or weekly shows
	new_data = []

	
	for show in shows:
		if show['origin_country']:
			if str(show['origin_country'][0]) == 'US':
				new_data.append(show)

	return new_data

def getAirsWeek(page):
	# converts int page to string
	page = str(page)
	# gets memcache to return that if exist
	data = memcache.get('weeklyTV' + page)
	url = "https://api.themoviedb.org/3/tv/on_the_air?page=" + page +"&language=en-US&api_key=" + TMDB_API_KEY
	if data is not None:
		return data['results'], data['total_pages']
	else:
		result = urlfetch.fetch(url)
		if result.status_code == 200:
			data = json.loads(result.content)
			if len(data['results']) > 0:
				memcache.add('weeklyTV' + page, data, time=CACHE_TIME)
				return data['results'], data['total_pages']
			else:
				return None

def getDetails(id, media):
	if media == 'tv':
		return getSingleShowInfo(id)
	elif media == 'movie':
		return getMovieDetails(id)
	else:
		return getSingleShowInfo(id) 
	

def getSingleShowInfo(id):
	show = []
	id = str(id)
	data = memcache.get('Single_Show' + id)
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
						memcache.add('Single_Show' + id,show,time=3600)
						return show
					else:
						return None
		except urlfetch.Error:
				logging.exception('Caught exception fetching url')

def getMovieDetails(id):
	movie = []
	id = str(id)
	data = memcache.get('Single_movie' + id)
	if data is not None:
		return data
	else:
		try:
			url = 'https://api.themoviedb.org/3/movie/'+ id +'?api_key=' + TMDB_API_KEY + '&language=en-US'
			result = urlfetch.fetch(url)
			if result.status_code == 200:
				data = json.loads(result.content)
				if len(data) > 0:
					movie.append(data)
					memcache.add('Single_movie' + id, movie, time=CACHE_TIME)
					return movie
				else:
					return None
		except urlfetch.Error:
				logging.exception('Caught exception fetching url')


# used for testing stuff
# def getShowTest(page):
# 	totalShows = []
# 	getAirsToday(1, totalShows)
# 	page = str(page)
# 	url = "https://api.themoviedb.org/3/tv/airing_today?page=" + page + "&language=en-US&api_key=" + TMDB_API_KEY
# 	url2 = "https://api.themoviedb.org/3/tv/airing_today?api_key=aa&language=en-US&page=2"
# 	result = urlfetch.fetch(url)
# 	result2 = urlfetch.fetch(url2)
# 	if result.status_code == 200:
# 		data = json.loads(result.content)
# 		data2 = json.loads(result2.content)
# 		newData = dict(data.items() + data2.items())
# 		return newData['results'], data['total_pages']


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




def getSearched(search):
	search = search.replace(' ', '%20')
	#url = 'https://api.themoviedb.org/3/search/tv?&query=' + search +'&language=en-US&api_key=' + TMDB_API_KEY
	url = 'https://api.themoviedb.org/3/search/multi?api_key=' + TMDB_API_KEY + '&language=en-US&query=' + search +'&include_adult=false'
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

# @app.template_filter('datetime')
# def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
#     return value.strftime(format)