from google.appengine.ext import ndb
import model

  
class UserComments(model.Base):
	user_key = ndb.KeyProperty(kind=model.User, required=True)
	showId = ndb.StringProperty(required=True)
	body = ndb.StringProperty(required=True)
	creator = ndb.StringProperty(required=True)
	#created = ndb.DateTimeProperty(auto_now = True)



class tvShows(model.Base):
	user_key = ndb.KeyProperty(kind=model.User, required=True)
	showId = ndb.StringProperty(required=True)
	showName = ndb.StringProperty(required=True)
	showPoster = ndb.StringProperty()
	favorite = ndb.BooleanProperty()
	



class BlogEntry(model.Base):
	user_key = ndb.KeyProperty(kind=model.User, required=True)
	
	title = ndb.StringProperty(required=True)
	body = ndb.TextProperty(required=True)
	created = ndb.DateTimeProperty(auto_now = True)