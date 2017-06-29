from flask import Blueprint
import flask
import model
from wtforms import Form, validators, StringField,TextAreaField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import auth

blog = Blueprint('blog', __name__, template_folder='templates')

class BlogEntryForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	body = TextAreaField('Body', validators=[DataRequired()])


@blog.route('/blog/')
def main_blog():
	blog_db, blog_cursor = model.BlogEntry.get_dbs(order='-created')
	return flask.render_template('blog.html', html_class='blog-list', blog_db=blog_db)

@blog.route('/blog/new/', methods=['GET', 'POST'])
@auth.admin_required
def new_blog():
	form = BlogEntryForm()
	
	if form.validate_on_submit(): 
		flask.flash("Blog entry, " + form.title.data + ", was created.", category='success')
		blogs_db = model.BlogEntry(user_key=auth.current_user_key(),title=form.title.data,body=form.body.data,)
		blogs_db.put()
		
		return flask.redirect(flask.url_for('blog.main_blog'))

	return flask.render_template('newblog.html',
												html_class='new-blog',
												form = form,)

@blog.route('/blog/<int:blog_id>/')
def blog_entry(blog_id):
	blog_db = model.BlogEntry.get_by_id(blog_id)
	if not blog_db:
		flask.abort(404)

	return flask.render_template('blog_view.html', html_class='blog-view',blog=blog_db)

@blog.route('/blog/<int:blog_id>/edit/', methods=['GET', 'POST'])
@auth.admin_required
def edit_blog(blog_id):
	blog_db = model.BlogEntry.get_by_id(blog_id)
	if not blog_db:
		flask.abort(404)
	form = BlogEntryForm(obj=blog_db)
	if form.validate_on_submit():
		form.populate_obj(blog_db)
		blog_db.put()
		return flask.redirect(flask.url_for('blog.blog_entry', blog_id=blog_db.key.id()))

	return flask.render_template('blog_edit.html', html_class='blog-edit',form=form)