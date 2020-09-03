#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, Blueprint
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app, session_options={'expire_on_commit': False})
migrate = Migrate(app, db)

# done - connect to a local postgresql database

bp = Blueprint('bp', __name__)
app.register_blueprint(bp)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

Shows = db.Table('Shows',
                 db.Column('venue_id', db.Integer, db.ForeignKey(
                     'Venue.id'), primary_key=True),
                 db.Column('artist_id', db.Integer, db.ForeignKey(
                     'Artist.id'), primary_key=True),
                 db.Column('start_time', db.DateTime, default=datetime.utcnow()
                           ))


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String()))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120), index=True)
    state = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(100))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    artists = db.relationship("Artist", secondary=Shows,
                              backref=db.backref('Venue',
                                                 cascade="all,delete"), lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.Text))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(100))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text)
    venues = db.relationship("Venue", secondary=Shows,
                             backref="Artist", lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO: Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@ app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@ app.route('/venues')
def venues():
    # done - replace with real venues data.
    data = []
    try:
        venues = Venue.query.distinct(Venue.city, Venue.state).all()
        if venues:
            for venue in venues:
                upcoming_shows = len(Venue.query.join(Shows).filter(Shows.c.start_time > datetime.utcnow(),
                                                                    Shows.c.venue_id == venue.id).all())
                data.append({
                    'city': venue.city,
                    'state': venue.state,
                    'venues': [{
                        'id': v.id,
                        'name': v.name,
                        'num_upcoming_shows': upcoming_shows
                    }for v in Venue.query.filter_by(city=venue.city, state=venue.state).all()]
                })
    except Exception as error:
        print(error)
        pass
    return render_template('pages/venues.html', areas=data)


@ app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get("search_term", "")
    data = []
    search_results = Venue.query.filter(
        Venue.name.ilike(f"%{search_term}%")).all()

    for venue in search_results:
        data.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(Venue.query.join(Shows).filter(Shows.c.start_time > datetime.utcnow(),
                                                                     Shows.c.venue_id == venue.id).all())
        })
        print(data)

    response = {
        'count': len(search_results),
        'data': data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.filter_by(id=venue_id).first()
    data = None

    shows = db.session.query(Shows).filter(Shows.c.venue_id == venue.id).all()
    past_shows = []
    upcoming_shows = []

    for show in shows:
        artist = Artist.query.filter_by(id=show.artist_id).first()

        show_info = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        }

        if show.start_time < datetime.utcnow():
            past_shows.append(show_info)
        elif show.start_time >= datetime.utcnow():
            upcoming_shows.append(show_info)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Done insert form data as a new Venue record in the db, instead
    # Done modify data to be the data object returned from db insertion
    form = VenueForm()

    name = form.name.data
    genres = form.genres.data
    phone = form.phone.data
    address = form.address.data
    city = form.city.data
    state = form.state.data
    website = form.website.data
    image_url = form.image_link.data
    facebook_url = form.facebook_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data

    new_venue = Venue(name=name, genres=genres, city=city, state=state, address=address, phone=phone, website=website,
                      image_link=image_url, facebook_link=facebook_url, seeking_talent=seeking_talent, seeking_description=seeking_description)

    try:
        db.session.add(new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + name + ' was successfully listed!')
    # Done on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except Exception as error:
        db.session.rollback()
        flash('An error occurred. Venue ' + name + ' could not be listed.')
        db.session.flush()
        print(error)
    return render_template('pages/home.html')


@ app.route('/venues/<int:venue_id>', methods=['POST'])
def delete_venue(venue_id):
    # DONE: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue is removed.')
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    # DONE: replace with real data returned from querying the database
    artists = Artist.query.all()
    data = []
    try:
        if artists:
            for artist in artists:
                filtered_artist = {
                    'id': artist.id,
                    'name': artist.name
                }

                data.append(filtered_artist)

    except Exception as error:
        print(error)
        pass

    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    data = []
    response = None

    artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

    for artist in artists:
        search_result = {
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(Artist.query.join(Shows).filter(Shows.c.start_time > datetime.utcnow(), Shows.c.artist_id == artist.id).all())
        }

        data.append(search_result)

    response = {
        'count': len(data),
        'data': data
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # Done: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.filter_by(id=artist_id).first()
    data = None

    shows = db.session.query(Shows).filter(
        Shows.c.artist_id == artist_id).all()

    past_shows = []
    upcoming_shows = []

    for show in shows:
        venue = Venue.query.filter_by(id=show.venue_id).first()

        show_info = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": format_datetime(str(show.start_time))
        }

        if show.start_time < datetime.utcnow():
            past_shows.append(show_info)
        elif show.start_time >= datetime.utcnow():
            upcoming_shows.append(show_info)

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'image_link': artist.image_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    form = ArtistForm()

    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    # DON: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()

    artist = Artist.query.filter_by(id=artist_id).first()

    artist.name = form.name.data
    artist.genres = form.genres.data
    artist.phone = form.phone.data
    artist.address = form.address.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.website = form.website.data
    artist.image_url = form.image_link.data
    artist.facebook_url = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    db.session.add(artist)
    db.session.commit()

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()

    form.name.data = venue.name
    form.genres.data = venue.genres
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

    # DONE: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm()

    venue = Venue.query.filter_by(id=venue_id).first()

    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.phone = form.phone.data
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.website = form.website.data
    venue.image_url = form.image_link.data
    venue.facebook_url = form.facebook_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    db.session.add(venue)
    db.session.commit()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    db.create_all(app=app)
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
