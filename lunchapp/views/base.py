# -*- coding:utf-8 -*-
from flask import Blueprint, request, jsonify, g, make_response
from flask.views import MethodView
from flask_login import login_user, logout_user, login_required
from ..model.user import *
from ..model.restaurant import *
from ..model import db_add
from .. import json_data
from flask.ext.bcrypt import Bcrypt

bcrypt = Bcrypt()


try:
    import simplejson as json
except:
    import json

bp = Blueprint('base', __name__)


class Login(MethodView):
    def post(self):
        phone = request.form.get("phone", None)
        password = request.form.get("password", None)
        user = User.query.filter_by(tel_num=phone).first()
        if not user:
            return make_response('No such user!', 404)
        if bcrypt.check_password_hash(user.password, password):
            login_user(user)
            g.user = user
            data = json_data.user_dict(user)
            return jsonify(data)
        else:
            return make_response("phone number and password doesn't match", 400)

bp.add_url_rule("/login", view_func=Login.as_view("login"))


class Logout(MethodView):
    def put(self):
        logout_user()
        return 'Logout Success!'

bp.add_url_rule("/logout", view_func=Logout.as_view("logout"))


class SignUp(MethodView):
    def post(self):
        phone = request.form.get("phone", None)
        password = request.form.get("password", None)
        name = request.form.get("name", None)
        if phone is None or password is None:
            return make_response('phone and password can not be None', 400)
        if name is None:
            name = phone
        user = User.query.filter_by(tel_num=phone).first()
        if user is not None:
            return make_response('User already exits', 401)
        user = User(name=name, tel_num=phone, password=bcrypt.generate_password_hash(password))
        db_add(user, commit=True)
        data = json_data.user_dict(user)
        return jsonify(data)

bp.add_url_rule("/signup", view_func=SignUp.as_view("signup"))


class PersonalRestaurantList(MethodView):
    @login_required
    def get(self):
        user = g.user
        restaurants = user.restaurants
        data = json_data.restaurant_dict(restaurants)
        return jsonify(result=data)

bp.add_url_rule("/myrestaurants", view_func=PersonalRestaurantList.as_view("myrestaurants"))


class PostNewRestaurant(MethodView):
    @login_required
    def post(self):
        user = g.user
        keys = ('name', 'content', 'address', 'spicy_level', 'cuisine')
        args = {}
        for key in keys:
            value = request.form.get(key, None)
            args.update({key: value})
        name = request.form.get('name', None)
        if name is None:
            return make_response('restaurant name is required!', 400)
        res = Restaurant.query.filter_by(name=name).first()
        if res:
            return make_response('restaurant already exits', 400)
        spicy = request.form.get('spicy_level', None)
        if spicy is not None and spicy not in (u'0', u'1', u'2', u'3'):
            return make_response('spicy_level should be in (0, 1, 2, 3)', 400)
        restaurant = Restaurant(**args)
        images = request.form.getlist('images[]', None)
        dbimage = []
        if images is not None:
            for imageurl in images:
                temp = Image(image_url=imageurl)
                restaurant.images.append(temp)
                dbimage.append(temp)
            db_add(dbimage, commit=True)
        user.restaurants.append(restaurant)
        db_add(user, commit=True)
        db_add(restaurant, commit=True)
        return jsonify(result='Add Success!')

bp.add_url_rule("/newrestaurant", view_func=PostNewRestaurant.as_view("newrestaurant"))


class UpdateRestaurant(MethodView):
    @login_required
    def post(self):
        user = g.user
        rid = request.form.get('rid', None)
        if rid is None:
            return make_response('rid is required', 400)
        restaurant = Restaurant.query.get(rid)
        if restaurant is None:
            return make_response("Restaurant not exist", 404)
        if restaurant not in user.restaurants:
            return make_response("Permission deny", 403)
        keys = ('name', 'content', 'address', 'spicy_level', 'cuisine')
        args = {}
        for key in keys:
            value = request.form.get(key, None)
            if value is not None:
                args.update({key: value})
        restaurant.update(**args)
        images = request.form.getlist('images[]', None)
        dbimage = []
        if images is not None:
            for imageurl in images:
                temp = Image(image_url=imageurl)
                restaurant.images.append(temp)
                dbimage.append(temp)
            db_add(dbimage, commit=True)
        db_add(restaurant, commit=True)
        return jsonify(result='Update Success!')

bp.add_url_rule("/updaterestaurant", view_func=UpdateRestaurant.as_view("updaterestaurant"))


class RestaurantPlaza(MethodView):
    @login_required
    def get(self):
        user = g.user
        resall = set(Restaurant.query.all())
        recommend = resall - set(user.restaurants)
        recommend = list(recommend)
        recommend = sorted(recommend, key=lambda x: x.create_time, reverse=True)
        recommend = json_data.restaurant_dict(recommend)
        return jsonify(result=recommend)

bp.add_url_rule("/restaurantplaza", view_func=RestaurantPlaza.as_view("restaurantplaza"))


class QiniuToken(MethodView):
    @login_required
    def get(self):
        from .utils import get_qiniu_token
        return jsonify(qiniu_token=get_qiniu_token())

bp.add_url_rule("/getqiniutoken", view_func=QiniuToken.as_view("getqiniutoken"))
