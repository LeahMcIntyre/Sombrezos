from datetime import datetime
from flask_wtf import Form
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, AnyOf, URL


class VendorForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    category = SelectField(
        # TODO implement enum restriction
        'category', validators=[DataRequired()],
        choices=[
            ('Sit-down', 'Sit-down'),
            ('Counter', 'Counter'),
            ('Drive-thru', 'Drive-thru'),

        ]
    )
    
    location = StringField(
        # TODO implement enum restriction
        'location', validators=[URL()]
    )

class UserForm(Form):
    username = StringField(
        'username', validators=[DataRequired()]
    )
    favorites = StringField(
        'favorites', validators=[DataRequired()]
    )

class DealForm(Form):
    items = StringField(
        'items', validators=[DataRequired()]
    )
    price = IntegerField(
        'price', validators=[DataRequired()]
    )
    pointsRequired = IntegerField(
        'pointsRequired', validators=[DataRequired()]
    )
    vendorID = IntegerField(
        'vendorID', validators=[DataRequired()]
    )


# TODO IMPLEMENT NEW ARTIST FORM AND NEW SHOW FORM
