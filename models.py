#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Match(db.Model):
    """比赛模型"""
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, comment='比赛名称')
    map = db.Column(db.String(100), nullable=False, comment='地图')
    date = db.Column(db.DateTime, default=datetime.utcnow, comment='比赛日期')
    file_path = db.Column(db.String(500), nullable=False, comment='Excel文件路径')
    
    # 队伍信息
    team_a_name = db.Column(db.String(100), nullable=False, comment='队伍A名称')
    team_b_name = db.Column(db.String(100), nullable=False, comment='队伍B名称')
    team_a_score = db.Column(db.Integer, default=0, comment='队伍A得分')
    team_b_score = db.Column(db.Integer, default=0, comment='队伍B得分')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    player_matches = db.relationship('PlayerMatch', backref='match', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'map': self.map,
            'date': self.date.strftime('%Y-%m-%d %H:%M'),
            'file_path': self.file_path,
            'team_a_name': self.team_a_name,
            'team_b_name': self.team_b_name,
            'team_a_score': self.team_a_score,
            'team_b_score': self.team_b_score,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Player(db.Model):
    """选手模型"""
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='选手姓名')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    matches = db.relationship('PlayerMatch', backref='player', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class PlayerMatch(db.Model):
    """选手比赛记录模型"""
    __tablename__ = 'player_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    team = db.Column(db.String(1), nullable=False, comment='队伍标识 A/B')
    
    # 比赛数据
    kills = db.Column(db.Integer, default=0, comment='击杀数')
    deaths = db.Column(db.Integer, default=0, comment='死亡数')
    assists = db.Column(db.Integer, default=0, comment='助攻数')
    headshots = db.Column(db.Integer, default=0, comment='爆头数')
    first_kills = db.Column(db.Integer, default=0, comment='首杀数')
    
    # 新增高级统计数据
    rws = db.Column(db.Float, default=0.0, comment='RWS')
    rating = db.Column(db.Float, default=0.0, comment='Rating')
    rating_plus = db.Column(db.Float, default=0.0, comment='Rating+')
    adr = db.Column(db.Float, default=0.0, comment='ADR')
    headshot_rate = db.Column(db.Float, default=0.0, comment='爆头率')
    kast = db.Column(db.Float, default=0.0, comment='KAST')
    sniper_kills = db.Column(db.Integer, default=0, comment='狙杀数')
    first_deaths = db.Column(db.Integer, default=0, comment='首死数')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一约束：每个选手在每场比赛中只能有一条记录
    __table_args__ = (db.UniqueConstraint('player_id', 'match_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'match_id': self.match_id,
            'team': self.team,
            'kills': self.kills,
            'deaths': self.deaths,
            'assists': self.assists,
            'headshots': self.headshots,
            'first_kills': self.first_kills,
            'rws': self.rws,
            'rating': self.rating,
            'rating_plus': self.rating_plus,
            'adr': self.adr,
            'headshot_rate': self.headshot_rate,
            'kast': self.kast,
            'sniper_kills': self.sniper_kills,
            'first_deaths': self.first_deaths,
            'kd_ratio': round(self.kills / max(self.deaths, 1), 2),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }