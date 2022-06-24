#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
from flask import request, abort, g, current_app
import time
from .user_mixin import UserMixin


class LoginManager(object):
    __SET = 'set'
    __CLEAR = 'clear'

    __user_loader_dict = {}
    __after_request_func_list = []
    __hash_generators = {}

    __instance_pool = dict()

    def __init__(self, app=None, role='default', expires=3600, salt=''):

        if app is not None:
            app.context_processor(LoginManager.__user_context_processor)
            app.after_request(LoginManager.__after_request_funcs)

        if self not in LoginManager.__instance_pool:
                if role in LoginManager.__instance_pool.values():
                    raise ValueError("Duplicate role name.")

        LoginManager.__instance_pool[self] = role

        self.__role = role
        self.__expires = expires
        self.__salt = salt
        self.__failure_handler = None

    def init_app(self, app):
        if app is None:
            raise ValueError('app must be set')
        app.context_processor(LoginManager.__user_context_processor)
        app.after_request(LoginManager.__after_request_funcs)

    # 通过密码校验后，调用这个方法载入用户信息
    def login(self, user):

        g.option = LoginManager.__SET
        g.uid = LoginManager.get_id(user)
        g.start_time = int(time.time()) + self.__expires

        LoginManager.__after_request_func_list.append(self.__set_cookie)

    # 登出当前用户
    def logout(self):
        g.option = LoginManager.__CLEAR
        LoginManager.__after_request_func_list.append(self.__set_cookie)

    def __set_cookie(self, resp):

        if hasattr(g, 'option'):

            if g.option == LoginManager.__SET:

                user = LoginManager.__user_loader_dict.get(self.__role)(g.uid)

                if user is not None:
                    info = [str(LoginManager.get_id(user)), str(g.start_time), LoginManager.__hash_generators.get(self.__role)(user)]
                    value = '-'.join(info)

                    httponly = current_app.config['SESSION_COOKIE_HTTPONLY']
                    secure = current_app.config['SESSION_COOKIE_SECURE']

                    resp.set_cookie(key=self.__role, value=value, expires=g.start_time, httponly=httponly, secure=secure)

            elif g.option == LoginManager.__CLEAR:

                resp.delete_cookie(key=self.__role)

        return resp

    @property
    def role(self):
        return self.__role

    @role.setter
    def role(self, role):
        self.__role = role

    @property
    def expires(self):
        return self.__expires

    @expires.setter
    def expires(self, expires):
        self.__expires = expires

    @property
    def salt(self):
        return self.__salt

    @salt.setter
    def salt(self, salt):
        self.__salt = salt

    # 获取当前用户
    @property
    def current_user(self):
        return LoginManager.__load_user_from_cookie(self.__role)

    # 是个装饰器，login_required 装饰器校验失败后调用其装饰的方法，可以分别制定以处理请求来自 WEB 和 API 的情况
    def failure_handler(self, handler):
        self.__failure_handler = handler
        return handler

    # 载入用户信息的回调方法，是个装饰器
    def user_loader(self, loader):

        LoginManager.__user_loader_dict[self.__role] = loader

        return loader

    # 载入 hash 校验值的回调方法，是个装饰器
    def hash_generator(self, generator):

        LoginManager.__hash_generators[self.__role] = generator

        return generator

    # 装饰器，用来给路由添加登陆校验功能
    def login_required(self, *permissions):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kw):
                if self.has_permissions(*permissions):
                    return func(*args, **kw)

                if self.__failure_handler is not None:
                    return self.__failure_handler()

                abort(401)

            return wrapper

        return decorator

    @staticmethod
    def role_required(*managers):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kw):
                authorized = False
                for manager in managers:
                    if not isinstance(manager, LoginManager):
                        raise ValueError('Instance of `LoginManager` required.')

                    if manager.current_user is not None:
                        authorized = True
                        break

                if authorized:
                    return func(*args, **kw)

                abort(401)

            return wrapper
        return decorator

    def has_permissions(self, *permissions):
        user = self.current_user

        if user is not None:
            for p in permissions:
                if (user.get_permissions() & p) != p:
                    return False
            return True
        return False

    @staticmethod
    def get_id(user):
        try:
            func = getattr(user, "get_id")
        except AttributeError:
            raise NotImplementedError
        else:
            return func()

    @staticmethod
    def __load_user_from_cookie(role):

        __CACHE_KEY_ROLE = 'cache_key_' + role

        if hasattr(g, __CACHE_KEY_ROLE):
            return getattr(g, __CACHE_KEY_ROLE)

        if LoginManager.__user_loader_dict.get(role) is None:
            raise NotImplementedError('user_loader must be set!')

        if LoginManager.__hash_generators.get(role, None) is None:
            raise NotImplementedError('hash_generator must be set!')

        cookie = request.cookies.get(role)

        if cookie is not None:
            info = cookie.split('-')
            if len(info) == 3:
                uid = info[0]
                expires = info[1]
                hash_client = info[2]

                if int(expires) > time.time():
                    user = LoginManager.__user_loader_dict.get(role)(uid)

                    if user is not None:
                        hash_server = LoginManager.__hash_generators.get(role)(user)
                        if hash_client == hash_server:
                            setattr(g, __CACHE_KEY_ROLE, user)
                            return user

        return None

    @staticmethod
    def __user_context_processor():
        return dict(current_user=LoginManager.__load_user_from_cookie)

    @staticmethod
    def __after_request_funcs(resp):

        for func in LoginManager.__after_request_func_list:
            func(resp)

        LoginManager.__after_request_func_list.clear()

        return resp


__all__ = [
    LoginManager.__name__,
    LoginManager.role_required.__name__,
    UserMixin.__name__,
]
