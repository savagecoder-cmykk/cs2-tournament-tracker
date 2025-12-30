#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Match, Player, PlayerMatch

# 确保使用绝对路径创建数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cs2_tournament.db')

with app.app_context():
    db.create_all()
    print('数据库表创建完成')
    print(f'数据库路径: {app.config["SQLALCHEMY_DATABASE_URI"]}')