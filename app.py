#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy.orm import backref
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migration = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
#Table that stores the vendors that each user marks as a favorite
favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('User.id'), primary_key=True),
    db.Column('vendor_id', db.Integer, db.ForeignKey('Vendor.id'), primary_key=True)
    )

#Table that stores the userid, vendor id, and the reward points that user has for that vendor
rewards = db.Table('rewards',
    db.Column('user_id', db.Integer, db.ForeignKey('User.id'), primary_key=True),
    db.Column('vendor_id', db.Integer, db.ForeignKey('Vendor.id'), primary_key=True),
    db.Column('points', db.Integer)
    )

#Table for user
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique = True)
    favorites = db.relationship('Vendor', secondary=favorites, lazy='subquery', backref=db.backref('favUsers', lazy=True))
    rewards = db.relationship('Vendor', secondary=rewards, lazy='subquery', backref=db.backref('users', lazy=True))

class Vendor(db.Model):
    __tablename__ = 'Vendor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    menu = db.Column(db.String(300))
    cost = db.Column(db.Integer)
    purchase_to_points = db.Column(db.Integer)
    category = db.Column(db.String(120))
    cuisine = db.Column(db.String)
    location = db.Column(db.String(200))
    offers = db.relationship('Deals', backref = 'vendor', lazy=True)
    menuItems = db.relationship('Menu', backref = backref('vendor', uselist = False), lazy=True)

class Deals(db.Model):
    __tablename__ = 'Deals'
    id = db.Column(db.Integer, primary_key = True)
    items = db.Column(db.String)
    price = db.Column(db.Integer)
    points_required = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer, db.ForeignKey('Vendor.id'), nullable=False)

class Menu(db.Model):
    __tablename__ = 'Menu'
    id = db.Column(db.Integer, primary_key = True)
    item = db.Column(db.String(120), nullable = False)
    price = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer, db.ForeignKey('Vendor.id'), nullable=False)


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  recentVendors = Vendor.query.order_by(db.desc(Vendor.id)).limit(10).all()
  #recentArtists = Artist.query.order_by(db.desc(Artist.id)).limit(10).all()
  return render_template('pages/home.html',vendors = recentVendors)


#  Vendors
#  ----------------------------------------------------------------

@app.route('/vendors')
def vendors():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = Vendor.query.order_by(db.desc(Vendor.id))

  return render_template('pages/vendors.html', vendors=data);

@app.route('/vendors/search', methods=['POST'])
def search_vendors():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  results = Vendor.query.filter(Vendor.name.ilike('%{}%'.format(request.form['search_term']))).all()
  response={
    "count": len(results),
    "data": []
    }
  for vendor in results:
    response["data"].append({
        "id": vendor.id,
        "name": vendor.name
      })

  return render_template('pages/search_vendors.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/vendors/<int:vendor_id>')
def show_vendor(vendor_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  vendor = Vendor.query.get(vendor_id)
  
  menuItems = vendor.menuItems

  data={
    "id": vendor.id,
    "name": vendor.name,
    "category": vendor.category,
    "location": vendor.location,
    "menu": vendor.menuItems
  }
  return render_template('pages/show_vendor.html', vendor=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/vendors/create', methods=['GET'])
def create_vendor_form():
  form = VendorForm()
  return render_template('forms/new_vendor.html', form=form)

@app.route('/vendors/create', methods=['POST'])
def create_vendor_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  new_vendor = Vendor()
  new_vendor.name = request.form['name']
  new_vendor.category = request.form['category']
  new_vendor.location = request.form['location']

  try:
    db.session.add(new_vendor)
    db.session.commit()
    # on successful db insert, flash success
    flash('Vendor ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Vendor ' + request.form['name'] + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return redirect(url_for('index'))

#  delete Vendor need to  figure out
#  ----------------------------------------------------------------
@app.route('/vendors/delete/<int:vendor_id>', methods=['POST'])
def delete_venue():
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  vendor_id = request.form.get('vendor_id')
  deleted_vendor = Vendor.query.get(id)
  vendorName = deleted_vendor.name
  try:
    db.session.delete(deleted_vendor)
    db.session.commit()
    flash('Vendor ' + vendorName + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('please try again. Vendor ' + vendorName + ' could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/users')
def users():
  # TODO: replace with real data returned from querying the database
  data= User.query.with_entities(User.id, User.username).all()
  return render_template('pages/users.html', users=data)

@app.route('/users/search', methods=['POST'])
def search_users():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  results = User.query.filter(User.username.ilike('%{}%'.format(request.form['search_term']))).all()

  response={
    "count": len(results),
    "data": []
  }
  for user in results:
    response['data'].append({
      "id": user.id,
      "name": user.username,
      })
  return render_template('pages/search_users.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  shows = artist.shows
  past_shows = []
  upcoming_shows = []
  for show in shows:
    show_info = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time)
    }
    if(show.upcoming):
      upcoming_shows.append(show_info)
    else:
      past_shows.append(show_info)
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description":artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)


@app.route('/users/create', methods=['GET'])
def create_user_form():
  form = UserForm()
  return render_template('forms/new_user.html', form=form)

@app.route('/users/create', methods=['POST'])
def create_user_submission():
  new_user = User()
 # new_artist.name = request.form['name']
  new_user.username = request.form['username']
  new_user.favorites = request.form['favorites']
  try:
    db.session.add(new_user)
    db.session.commit()
    # on successful db insert, flash success
    flash('User ' + request.form['username'] + ' was successfully added!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + new_user.username + ' could not be added.')
  finally:
    db.session.close()
  return redirect(url_for('index'))
#  delete artist
#  ----------------------------------------------------------------
@app.route('/artists/delete', methods=['POST'])
def delete_artist():
  artist_id = request.form.get('artist_id')
  deleted_artist = Artist.query.get(artist_id)
  artistName = deleted_artist.name
  try:
    db.session.delete(deleted_artist)
    db.session.commit()
    flash('Artist ' + artistName + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('please try again. Venue ' + artistName + ' could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/edit', methods=['GET'])
def edit_artist():
  form = ArtistForm()
  artist_id = request.args.get('artist_id')
  artist = Artist.query.get(artist_id)
  artist_info={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist_info)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)
  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.facebook_link = request.form['facebook_link']
  artist.genres = request.form['genres']
  artist.image_link = request.form['image_link']
  artist.website = request.form['website']
  try:
    db.session.commit()
    flash("Artist {} is updated successfully".format(artist.name))
  except:
    db.session.rollback()
    flash("Artist {} isn't updated successfully".format(artist.name))
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/edit', methods=['GET'])
def edit_venue():
  venue_id = request.args.get('venue_id')
  form = VendorForm()
  venue = Venue.query.get(venue_id)
  venue_info={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue_info)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.facebook_link = request.form['facebook_link']
  venue.genres = request.form['genres']
  venue.image_link = request.form['image_link']
  venue.website = request.form['website']
  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + new_venue.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Deals
#  ----------------------------------------------------------------

@app.route('/deals/create', methods=['GET'])
def create_deal_form():
  form = DealForm()
  return render_template('forms/new_deal.html', form=form)

@app.route('/deals/create', methods=['POST'])
def create_deals_submission():
  new_deal = Deals()
  new_deal.items = (request.form['items'])
  new_deal.price = int(request.form['price'])
  new_deal.pointsRequired = int(request.form['pointsRequired'])
  new_deal.vendorID = int(request.form['vendorID'])
  try:
    db.session.add(new_deal)
    db.session.commit()
    # on successful db insert, flash success
    flash('Deal ' + request.form['items'] + ' were successfully added!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Deal ' + new_deal.items + ' could not be added.')
  finally:
    db.session.close()
  return redirect(url_for('index'))


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  new_show = Show()
  new_show.artist_id = request.form['artist_id']
  new_show.venue_id = request.form['venue_id']
  dateAndTime = request.form['start_time'].split(' ')
  DTList = dateAndTime[0].split('-')
  DTList += dateAndTime[1].split(':')
  for i in range(len(DTList)):
    DTList[i] = int(DTList[i])
  new_show.start_time = datetime(DTList[0],DTList[1],DTList[2]
                                        ,DTList[3],DTList[4],DTList[5])
  now = datetime.now()
  new_show.upcoming = (now < new_show.start_time)
  try:
    db.session.add(new_show)
    # update venue and artist table
    updated_artist = Artist.query.get(new_show.artist_id)
    updated_venue = Venue.query.get(new_show.venue_id)
    if(new_show.upcoming):
      updated_artist.upcoming_shows_count += 1;
      updated_venue.upcoming_shows_count += 1;
    else:
      updated_artist.past_shows_count += 1;
      updated_venue.past_shows_count += 1;
    # on successful db insert, flash success
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('Show could not be listed. please make sure that your ids are correct')
  finally:
    db.session.close()
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
