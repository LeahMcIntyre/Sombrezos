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
    db.Column('user_id', db.Integer, db.ForeignKey('User.id', ondelete='CASCADE'), primary_key=True),
    db.Column('vendor_id', db.Integer, db.ForeignKey('Vendor.id', ondelete='CASCADE'), primary_key=True)
    )

#Attribute object to represent the points each user has with each vendor
class rewards(db.Model):
  __tablename__ = 'rewards'
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('User.id', ondelete='CASCADE'), primary_key=True)
  vendor_id = db.Column(db.Integer, db.ForeignKey('Vendor.id', ondelete='CASCADE'), primary_key=True)
  points = db.Column(db.Integer)

  user = db.relation('User', back_populates ='vendors')
  vendor = db.relationship('Vendor', back_populates='users')

#Table for Vendor
class Vendor(db.Model):
    __tablename__ = 'Vendor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    cost = db.Column(db.Integer)
    purchase_to_points = db.Column(db.Integer)
    category = db.Column(db.String(120))
    cuisine = db.Column(db.String)
    location = db.Column(db.String(200))
    offers = db.relationship('Deals', backref = 'vendor', lazy=True)
    menuItems = db.relationship('Menu', backref = backref('vendor', uselist = False), lazy=True, cascade="all, delete", passive_deletes=True)
    users = db.relationship('rewards', back_populates="vendor", cascade="all, delete",
        passive_deletes=True)

#Table for user
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique = True)
    favorites = db.relationship('Vendor', secondary=favorites, lazy='subquery', backref=db.backref('favUsers', lazy=True), cascade="all, delete", passive_deletes=True)
    vendors = db.relationship('rewards',back_populates = "user", cascade="all, delete", passive_deletes=True)


#Table for Deals
class Deals(db.Model):
    __tablename__ = 'Deals'
    id = db.Column(db.Integer, primary_key = True)
    item = db.Column(db.String)
    price = db.Column(db.Integer)
    points_required = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer, db.ForeignKey('Vendor.id'), nullable=False)

#Tables for Menu
class Menu(db.Model):
    __tablename__ = 'Menu'
    id = db.Column(db.Integer, primary_key = True)
    item = db.Column(db.String(120), nullable = False)
    price = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer, db.ForeignKey('Vendor.id', ondelete='CASCADE'), nullable=False)



#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  recentVendors = Vendor.query.order_by(db.desc(Vendor.id)).limit(10).all()
  return render_template('pages/home.html',vendors = recentVendors)


#  Vendors
#  ----------------------------------------------------------------

#Show all the vendors
@app.route('/vendors')
def vendors():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  vendors = Vendor.query.order_by(db.desc(Vendor.id))

  dealInfo = []
  result = db.session.query(Vendor).join(Deals).filter(Vendor.id == Deals.vendor_id).all()

  for row in result:
   for offer in row.offers:
      info = {
        "vendor_id" : row.id,
        "vendor_name": row.name,
        "deal_item" : offer.item,
        "deal_price": offer.price,
        "deal_points": offer.points_required
      }
      dealInfo.append(info)

  data = {
    "vendors" : vendors,
    "deals" : dealInfo
  }

  return render_template('pages/vendors.html', data=data);

#Search for vendors
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

#Show specific vendor with id = vendor_id
@app.route('/vendors/<int:vendor_id>')
def show_vendor(vendor_id):

  vendor = Vendor.query.get(vendor_id)
  
  menuItems = vendor.menuItems
  deals = vendor.offers
  fullMenu = []
  allDeals = []


  for menu in menuItems: 
    menu_info= {
      "menu_id": menu.id,
      "menu_item": menu.item,
      "menu_price": menu.price
    }
    fullMenu.append(menu_info)

  for deal in deals:
    deal_info={
      "item": deal.item,
      "price": deal.price,
      "points_required" : deal.points_required
    }
    allDeals.append(deal_info)

  data={
    "id": vendor.id,
    "name": vendor.name,
    "category": vendor.category,
    "location": vendor.location,
    "cuisine": vendor.cuisine,
    "cost": vendor.cost*'$',
    "purchase_to_points": vendor.purchase_to_points,
    "fullMenu": fullMenu,
    "allDeals" : allDeals
  }
  return render_template('pages/show_vendor.html', vendor=data)

# Insert A Vendor
@app.route('/vendors/create', methods=['GET'])
def create_vendor_form():
  form = VendorForm()
  return render_template('forms/new_vendor.html', form=form)

@app.route('/vendors/create', methods=['POST'])
def create_vendor_submission():
 
  new_vendor = Vendor()
  new_vendor.name = request.form['name']
  new_vendor.category = request.form['category']
  new_vendor.cost = request.form['cost']
  new_vendor.cuisine = request.form['cuisine']
  new_vendor.location = request.form['location']
  new_vendor.purchase_to_points = request.form['purchase_to_points']

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

#  Delete A Vendor
@app.route('/vendors/delete/<int:vendor_id>', methods=['GET', 'POST'])
def delete_vendor(vendor_id):

  deleted_vendor = Vendor.query.get(vendor_id)
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
  return redirect(url_for('index'))

#Update Vendor Record
@app.route('/vendors/<int:vendor_id>/edit', methods=['POST','GET'])
def edit_vendor(vendor_id):
  form = VendorForm()
  vendor = Vendor.query.get(vendor_id)
  data={
    "id": vendor.id,
    "name": vendor.name,
    "category": vendor.category,
    "location": vendor.location,
    "cuisine": vendor.cuisine,
    "cost" : vendor.cost*'$',
    "purchase_to_points" : vendor.purchase_to_points
  }
  print("editing")
  return render_template('forms/edit_vendor.html', form=form, vendor=data)

@app.route('/vendors/<int:vendor_id>/edit_info', methods=['POST'])
def edit_vendor_submission(vendor_id):
  vendor = Vendor.query.get(vendor_id)

  vendor.name = request.form['name']
  vendor.category = request.form['category']
  vendor.location = request.form['location']

  try:
    db.session.commit()
    flash('Vendor ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + vendor.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('vendors', vendor_id=vendor_id))

#  Users
#  ----------------------------------------------------------------

#Lists all the users
@app.route('/users')
def users():
  # TODO: replace with real data returned from querying the database
  data= User.query.with_entities(User.id, User.username).all()
  return render_template('pages/users.html', users=data)

#Searches all the users
@app.route('/users/search', methods=['POST'])
def search_users():
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

#Display infor for user with id = user_id
@app.route('/users/<int:user_id>')
def show_user(user_id):
  user = User.query.get(user_id)

  favorites = []
  for vendor in user.favorites:
    favorites.append(vendor.name)
  

  user={
    "username" : user.username,
    "id" : user.id,
    "rewards" : user.vendors,
    "favorites" : favorites
  }
  return render_template('pages/show_user.html', user=user)
  

#Insert A User
@app.route('/users/create', methods=['GET'])
def create_user_form():
  form = UserForm()
  return render_template('forms/new_user.html', form=form)

@app.route('/users/create', methods=['GET', 'POST'])
def create_user_submission():
  new_user = User()
  new_user.username = request.form['username']
  #new_user.favorites = request.form['favorites']
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


#  Creating and Updating Rewards
#  ----------------------------------------------------------------
@app.route('/vendors/<int:vendor_id>/purchase', methods = ['GET', 'POST'])
def create_purchase_form(vendor_id):

  vendor = Vendor.query.get(vendor_id)
  users = User.query.with_entities(User.id, User.username).all()

  menuItems = vendor.menuItems
  fullMenu = []

  for menu in menuItems: 
    menu_info= {
      "menu_id": menu.id,
      "menu_item": menu.item,
      "menu_price": menu.price
    }
    fullMenu.append(menu_info)

  user_info =[]
  for user in users:
    info = {
      "id": user.id,
      "username": user.username
    }
    user_info.append(info)
  
  data = {
    "users": user_info,
    "vendor_id": vendor.id,
    "menu" : fullMenu
  }
  return render_template('forms/purchase.html', data=data)

@app.route('/vendors/<int:vendor_id>/purchase_info', methods=['POST'])
def create_purchase_submission(vendor_id):
  print("oh no")
  user_id = request.form['user']
  vendor = Vendor.query.get(vendor_id)
  conversion = vendor.purchase_to_points
  user = User.query.get(user_id)

  print("help+me")
  print(user_id)
  purchase_items = request.form['items']
  price = 0

  for purchase_id in purchase_items:
    item = Menu.query.get(purchase_id)
    price = price + item.price

  new_points = price * conversion
  result = rewards.query.filter(rewards.vendor_id == vendor_id,  rewards.user_id == user_id).first()

  
  if result:
    result.points = result.points + new_points
    try:
      db.session.commit()
      # on successful db insert, flash success
      flash('Purchase Made')
    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('Purchase could not be made!')
    finally:
      db.session.close()
  else:
    new_rewards = rewards()
    new_rewards.vendor_id = vendor_id
    new_rewards.user_id = user_id
    new_rewards.points = new_points
    try:
      db.session.add(new_rewards)
      db.session.commit()
      # on successful db insert, flash success
      flash('Purchase Made')
    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('Purchase could not be made!')
    finally:
      db.session.close()
  return redirect(url_for('show_rewards', user_id=user_id))



#  Updating Rewards When Rewards Used To Purchase Deal
#  ----------------------------------------------------------------
@app.route('/vendors/<int:vendor_id>/purchase_deal', methods = ['GET', 'POST'])
def create_purchase_deal_form(vendor_id):

  vendor = Vendor.query.get(vendor_id)
  users = User.query.with_entities(User.id, User.username).all()

  deals = vendor.offers
  allDeals = []

  for deal in deals: 
    deal_info= {
      "id": deal.id,
      "item": deal.item,
      "price": deal.price
    }
    allDeals.append(deal_info)

  user_info =[]
  for user in users:
    info = {
      "id": user.id,
      "username": user.username
    }
    user_info.append(info)
  
  data = {
    "users": user_info,
    "vendor_id": vendor.id,
    "deals" : allDeals
  }
  return render_template('forms/purchase_deal.html', data=data)

@app.route('/vendors/<int:vendor_id>/purchase_deal_info', methods=['POST'])
def create_purchase_deal_submission(vendor_id):

  user_id = request.form['user']
  deal_id = request.form['item']

  vendor = Vendor.query.get(vendor_id)
  user = User.query.get(user_id)
  deal = Deals.query.get(deal_id)

  reward_points = rewards.query.filter(rewards.vendor_id == vendor_id,  rewards.user_id == user_id).first()

  if request.form['purchase_type'] == 'points':
    if reward_points.points >= deal.points_required:
      reward_points.points = reward_points.points - deal.points_required
      try:
        db.session.commit()
        flash('Purchase of Deal Logged')
      except:
        flash('Purchase could not be logged')
      finally:
        db.session.close()
    else:
      flash('Not enough points to purchase deal with points')
  
  
  return redirect(url_for('show_rewards', user_id=user_id))



#Display the rewards the user has with 
@app.route('/users/<int:user_id>/rewards')
def show_rewards(user_id):
  user = User.query.get(user_id)
  
  reward_info = []
  for reward in user.vendors:
    vendor = Vendor.query.get(reward.vendor_id)
    info = {
      "vendor": vendor.name, 
      "points": reward.points
    }
    reward_info.append(info)
    
  data = {
    "user": user_id,
    "reward_info" : reward_info
  }
  return render_template('pages/show_rewards.html',data = data)

#  Create Deals
 #  ----------------------------------------------------------------

@app.route('/deals/create', methods=['GET'])
def create_deal_form():
  form = DealForm()
  return render_template('forms/new_deal.html', form=form)

@app.route('/deals/create', methods=['POST'])
def create_deals_submission():
  new_deal = Deals()
  new_deal.item = (request.form['item'])
  new_deal.price = int(request.form['price'])
  new_deal.points_required = int(request.form['points_required'])
  new_deal.vendor_id = int(request.form['vendor_id'])
  try:
    db.session.add(new_deal)
    db.session.commit()
     # on successful db insert, flash success
    flash('Deal ' + request.form['item'] + ' were successfully added!')
  except:
    db.session.rollback()
     # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Deal ' + new_deal.item + ' could not be added.')
  finally:
    db.session.close()
  return redirect(url_for('index'))

#  Add or Delete Favorite Vendor
 #  ----------------------------------------------------------------
@app.route('/users/<int:user_id>/add_favorites', methods=['GET', 'POST'])
def create_add_favorites_form(user_id):

  vendors = Vendor.query.order_by(db.desc(Vendor.id))

  
  data = {
    "user_id" : user_id,
    "vendors" : vendors
  }

  return render_template('forms/new_favorite.html', data=data)

@app.route('/users/<int:user_id>/add_favorites_info', methods=['POST'])
def create_add_favorites_submission(user_id):
  
  vendor_id = request.form['vendor']
  statement = favorites.insert().values(user_id=user_id, vendor_id=vendor_id)
  try:
    db.session.execute(statement)
    db.session.commit()
    flash('Vendor was successfully added to favorites')
  except:
    db.session.rollback()
    flash('An error occurred. Vendor could not be added to favorites')
  finally:
    db.session.close()
  return redirect(url_for('index'))


@app.route('/users/<int:user_id>/delete_favorites', methods=['GET', 'POST'])
def create_delete_favorites_form(user_id):
  user = User.query.get(user_id)
  vendors = user.favorites
  vendor_info = []

  data = {
    "user_id" : user_id,
    "vendors" : vendors
  }
  return render_template('forms/delete_favorite.html', data=data)

@app.route('/users/<int:user_id>/delete_favorites_info', methods=['POST'])
def create_delete_favorites_submission(user_id):
  user = User.query.get(user_id)
  vendor_id = request.form['vendor']
  vendor = Vendor.query.get(vendor_id)
  user.favorites.remove(vendor)

  try:
    db.session.commit()
    flash('Vendor removed from favorites')
  except:
    db.session.rollback()
    flash('Vendor could not be removed from favorites')
  finally:
    db.session.close()
  return redirect(url_for('index'))


#  Add or Delete Menu Item 
 #  ----------------------------------------------------------------

@app.route('/vendors/<int:vendor_id>/add_menu_item', methods=['GET'])
def create_add_menu_form(vendor_id):
  form = DealForm()
  return render_template('forms/new_menu.html', form=form, vendor_id=vendor_id)

@app.route('/vendors/<int:vendor_id>/add_menu_item', methods=['POST'])
def create_add_menu_submission(vendor_id):
  new_menu = Menu()
  new_menu.item = (request.form['item'])
  new_menu.price = request.form['price']
  
  new_menu.vendor_id = vendor_id
  try:
    db.session.add(new_menu)
    db.session.commit()
     # on successful db insert, flash success
    flash('Item ' + request.form['item'] + ' were successfully added to the menu')
  except:
    db.session.rollback()
     # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Item ' + new_menu.item + ' could not be added to the menu')
  finally:
    db.session.close()
  return redirect(url_for('index'))

#Delete menu item
@app.route('/vendors/<int:vendor_id>/delete_menu_item', methods=['GET', 'POST'])
def create_delete_menu_form(vendor_id):
  vendor = Vendor.query.get(vendor_id)

  menuItems = vendor.menuItems
  fullMenu = []

  for menu in menuItems: 
    menu_info= {
      "menu_id": menu.id,
      "menu_item": menu.item,
      "menu_price": menu.price
    }
    fullMenu.append(menu_info)

  data = {
    "vendor_id" : vendor_id,
    "menu" : fullMenu
  }
  return render_template('forms/delete_menu.html', data=data)

@app.route('/vendors/<int:vendor_id>/delete_menu_info', methods=['POST'])
def create_delete_menu_item_submission(vendor_id):
  menu_id = request.form['item']
  deleted_menu = Menu.query.get(menu_id)
  try:
    db.session.delete(deleted_menu)
    db.session.commit()
    flash('Menu Item removed from Menu')
  except:
    db.session.rollback()
    flash('Item could not be removed from menu')
  finally:
    db.session.close()
  return redirect(url_for('vendors', vendor_id=vendor_id))

def find_similar_vendor(vendor_id):
  vendor = Vendor.query.get(vendor_id)
  




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
