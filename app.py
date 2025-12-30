#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import openpyxl
import pandas as pd
from models import db, Match, Player, PlayerMatch

app = Flask(__name__)
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cs2_tournament.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# 初始化数据库
db.init_app(app)

# 创建数据库表
with app.app_context():
    db.create_all()

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_excel_data(file_path):
    """解析Excel文件数据"""
    try:
        # 首先尝试使用pandas直接读取，如果失败则使用openpyxl
        try:
            data = pd.read_excel(file_path)
            print(f"使用pandas成功读取文件: {file_path}")
        except Exception as e1:
            print(f"pandas读取失败: {e1}，尝试使用openpyxl")
            # 使用openpyxl读取
            workbook = openpyxl.load_workbook(file_path)
            sheet_name = workbook.sheetnames[0]
            worksheet = workbook[sheet_name]
            
            # 转换为pandas DataFrame
            data = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"使用openpyxl成功读取文件: {file_path}")
        
        # 解析比赛数据
        match_info = parse_match_info(data)
        team_data = parse_team_data_new(data, match_info)
        
        return {
            'match_info': match_info,
            'team_data': team_data,
            'raw_data': data.to_dict('records')
        }
    except Exception as e:
        print(f"解析Excel错误: {e}")
        return None

def parse_match_info(data):
    """解析比赛基本信息"""
    match_info = {}
    
    # 查找地图信息
    for idx, row in data.iterrows():
        for col in data.columns:
            cell_value = str(row[col]).strip()
            if '地图' in cell_value and idx < len(data) - 1:
                map_value = str(data.iloc[idx + 1][col]).strip()
                if map_value and map_value != 'nan':
                    match_info['map'] = map_value
                    break
        if 'map' in match_info:
            break
    
    # 查找比赛名称
    for idx, row in data.iterrows():
        for col in data.columns:
            cell_value = str(row[col]).strip()
            if '对黑' in cell_value:
                match_info['name'] = cell_value
                break
        if 'name' in match_info:
            break
    
    # 设置默认值
    if 'map' not in match_info:
        match_info['map'] = 'Unknown'
    if 'name' not in match_info:
        match_info['name'] = f"比赛 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    return match_info

def parse_team_data_new(data, match_info):
    """解析队伍和选手数据 - 针对垂直布局Excel的新解析逻辑"""
    teams = {}
    
    try:
        print("开始解析新格式Excel文件...")
        
        # 解析比赛基本信息
        match_name = str(data.iloc[0, 0]).strip()  # 第0行第0列：比赛名称
        game_map = str(data.iloc[0, 1]).strip()    # 第0行第1列：地图
        
        print(f"比赛名称: {match_name}")
        print(f"地图: {game_map}")
        
        # 解析队伍A信息
        team_a_name = str(data.iloc[2, 0]).strip()  # 第2行第0列：队伍A
        team_a_score = str(data.iloc[2, 1]).strip() # 第2行第1列：13
        
        # 解析队伍B信息
        team_b_name = str(data.iloc[11, 0]).strip() # 第11行第0列：队伍B
        team_b_score = str(data.iloc[11, 1]).strip() # 第11行第1列：7
        
        print(f"队伍A: {team_a_name}, 得分: {team_a_score}")
        print(f"队伍B: {team_b_name}, 得分: {team_b_score}")
        
        # 获取列标题（第3行和第12行都是标题行，取第一个）
        headers = []
        for col_idx in range(len(data.columns)):
            header = str(data.iloc[3, col_idx]).strip()
            headers.append(header)
        
        print(f"列标题: {headers}")
        
        # 解析队伍A的选手数据（第4-8行）
        team_a_players = []
        for row_idx in range(4, 9):  # 第4-8行
            if row_idx < len(data):
                player_data = parse_player_from_row(data.iloc[row_idx], headers, f"队伍{team_a_name}")
                if player_data:
                    team_a_players.append(player_data)
                    print(f"队伍A选手: {player_data['name']}")
        
        # 解析队伍B的选手数据（第13-17行）
        team_b_players = []
        for row_idx in range(13, 18):  # 第13-17行
            if row_idx < len(data):
                player_data = parse_player_from_row(data.iloc[row_idx], headers, f"队伍{team_b_name}")
                if player_data:
                    team_b_players.append(player_data)
                    print(f"队伍B选手: {player_data['name']}")
        
        # 构建队伍数据
        if team_a_players:
            teams['A'] = {
                'name': team_a_name,
                'score': team_a_score,
                'players': team_a_players
            }
            
        if team_b_players:
            teams['B'] = {
                'name': team_b_name,
                'score': team_b_score,
                'players': team_b_players
            }
        
        print(f"解析完成: 队伍A {len(team_a_players)}人, 队伍B {len(team_b_players)}人")
        
        # 更新match_info
        match_info['name'] = match_name
        match_info['map'] = game_map
        
        return teams
        
    except Exception as e:
        print(f"新解析逻辑错误: {e}")
        import traceback
        traceback.print_exc()
        return parse_team_data(data, match_info)

def parse_player_from_row(row, headers, team_name):
    """从单行数据解析选手信息"""
    player_data = {}
    
    try:
        # 选手名称在第0列
        player_name = str(row.iloc[0]).strip()
        if not player_name or player_name == 'nan' or player_name == '选手名称':
            return None
        
        player_data['name'] = player_name
        player_data['team'] = team_name
        
        # 解析统计数据
        for col_idx, header in enumerate(headers):
            if col_idx >= len(row):
                continue
                
            value = str(row.iloc[col_idx]).strip()
            if value == 'nan' or not value:
                continue
            
            try:
                # 根据列标题解析数据
                if '击杀' in header and '爆头击杀' not in header and '首杀' not in header:
                    player_data['kills'] = int(float(value))
                elif '死亡' in header:
                    player_data['deaths'] = int(float(value))
                elif '助攻' in header:
                    player_data['assists'] = int(float(value))
                elif '爆头击杀' in header:
                    player_data['headshots'] = int(float(value))
                elif '首杀' in header:
                    player_data['first_kills'] = int(float(value))
                elif 'RWS' in header:
                    player_data['rws'] = float(value)
                elif 'Rating' in header:
                    if 'Rating+' in header:
                        player_data['rating_plus'] = float(value)
                    else:
                        player_data['rating'] = float(value)
                elif 'ADR' in header:
                    player_data['adr'] = float(value)
                elif '爆头率' in header:
                    player_data['headshot_rate'] = float(value)
                elif 'KAST' in header:
                    player_data['kast'] = float(value)
                elif '狙杀数' in header:
                    player_data['sniper_kills'] = int(float(value))
                elif '首死数' in header:
                    player_data['first_deaths'] = int(float(value))
            except Exception as e:
                print(f"解析选手{player_name}的{header}数据失败: {value}, 错误: {e}")
                continue
        
        # 设置默认值
        player_data.setdefault('kills', 0)
        player_data.setdefault('deaths', 0)
        player_data.setdefault('assists', 0)
        player_data.setdefault('headshots', 0)
        player_data.setdefault('first_kills', 0)
        player_data.setdefault('first_deaths', 0)
        player_data.setdefault('sniper_kills', 0)
        player_data.setdefault('rws', 0.0)
        player_data.setdefault('rating', 0.0)
        player_data.setdefault('rating_plus', 0.0)
        player_data.setdefault('adr', 0.0)
        player_data.setdefault('headshot_rate', 0.0)
        player_data.setdefault('kast', 0.0)
        
        return player_data
        
    except Exception as e:
        print(f"解析选手数据失败: {e}")
        return None

def parse_player_row_new(row, columns, headers):
    """解析单行选手数据 - 新逻辑"""
    player_data = {}
    
    # 查找选手名称（从数据列）
    data_column = None
    for col in columns:
        col_str = str(col).strip()
        if '对黑' in col_str:
            data_column = col
            break
    
    if not data_column:
        return None
    
    player_name = str(row[data_column]).strip()
    if not player_name or player_name == 'nan' or player_name == '选手名称':
        return None
    
    player_data['name'] = player_name
    
    # 使用headers（列标题）来匹配统计数据
    for i, col in enumerate(columns):
        value = str(row[col]).strip()
        
        if value == 'nan' or not value:
            continue
            
        # 获取对应的列标题
        header = headers[i] if i < len(headers) else ""
        
        try:
            # 根据列标题匹配统计数据
            if '击杀' in header and '爆头击杀' not in header and '首杀' not in header:
                player_data['kills'] = int(float(value))
            elif '死亡' in header:
                player_data['deaths'] = int(float(value))
            elif '助攻' in header:
                player_data['assists'] = int(float(value))
            elif '爆头击杀' in header:
                player_data['headshots'] = int(float(value))
            elif '首杀' in header:
                player_data['first_kills'] = int(float(value))
        except Exception as e:
            print(f"解析{player_data['name']}第{i}列数据失败: {value}, 错误: {e}")
            continue
    
    # 设置默认值
    player_data.setdefault('kills', 0)
    player_data.setdefault('deaths', 0)
    player_data.setdefault('assists', 0)
    player_data.setdefault('headshots', 0)
    player_data.setdefault('first_kills', 0)
    
    return player_data

def parse_player_row(row, columns):
    """解析单行选手数据"""
    player_data = {}
    
    # 查找选手名称
    for col in columns:
        col_str = str(col).strip()
        if '选手名称' in col_str:
            player_name = str(row[col]).strip()
            if player_name and player_name != 'nan' and player_name != '选手名称':
                player_data['name'] = player_name
                break
    
    # 如果没有找到选手名称，返回空
    if 'name' not in player_data:
        return None
    
    # 解析统计数据
    for col in columns:
        col_str = str(col).strip()
        value = str(row[col]).strip()
        
        if value == 'nan' or not value:
            continue
            
        try:
            if '击杀' in col_str:
                player_data['kills'] = int(value) if value.isdigit() else 0
            elif '死亡' in col_str:
                player_data['deaths'] = int(value) if value.isdigit() else 0
            elif '助攻' in col_str:
                player_data['assists'] = int(value) if value.isdigit() else 0
            elif '爆头' in col_str:
                player_data['headshots'] = int(value) if value.isdigit() else 0
            elif '首杀' in col_str:
                player_data['first_kills'] = int(value) if value.isdigit() else 0
        except:
            continue
    
    # 设置默认值
    player_data.setdefault('kills', 0)
    player_data.setdefault('deaths', 0)
    player_data.setdefault('assists', 0)
    player_data.setdefault('headshots', 0)
    player_data.setdefault('first_kills', 0)
    
    return player_data

def parse_team_data(data, match_info):
    """解析队伍和选手数据"""
    teams = {}
    
    # 查找包含"对黑"的列作为数据列，增加容错性
    data_column = None
    possible_columns = []
    
    for col in data.columns:
        col_str = str(col).strip()
        if '对黑' in col_str:
            possible_columns.append(col)
    
    # 如果找到多个可能的数据列，选择第一个
    if possible_columns:
        data_column = possible_columns[0]
    else:
        # 如果没有找到"对黑"列，尝试其他可能的标识
        for col in data.columns:
            col_str = str(col).strip()
            if any(keyword in col_str for keyword in ['A', 'B', '队伍', 'team', 'Team']):
                data_column = col
                break
    
    if not data_column:
        print("未找到数据列，尝试使用第一列")
        # 如果还是找不到，使用第一列作为数据列
        if len(data.columns) > 0:
            data_column = data.columns[0]
        else:
            print("数据为空")
            return teams
    
    # 解析队伍数据 - 改进的队伍识别逻辑
    team_data = parse_teams_with_improved_logic(data, data_column)
    
    # 如果改进逻辑解析失败，使用原有逻辑作为备选
    if not team_data:
        print("使用原有解析逻辑")
        # 解析队伍A数据
        team_a_players = parse_players_from_column(data, data_column, 'A')
        if team_a_players:
            teams['A'] = {
                'name': '队伍A',
                'players': team_a_players
            }
        
        # 解析队伍B数据
        team_b_players = parse_players_from_column(data, data_column, 'B')
        if team_b_players:
            teams['B'] = {
                'name': '队伍B',
                'players': team_b_players
            }
    else:
        teams = team_data
    
    return teams

def parse_teams_with_improved_logic(data, data_column):
    """改进的队伍解析逻辑"""
    teams = {}
    
    # 扫描整个数据，查找队伍标识
    team_positions = {}
    
    for idx, row in data.iterrows():
        for col in data.columns:
            cell_value = str(row[col]).strip()
            if cell_value in ['A', 'B']:
                if cell_value not in team_positions:
                    team_positions[cell_value] = []
                team_positions[cell_value].append((idx, col))
    
    # 解析每个队伍的数据
    for team_key in ['A', 'B']:
        if team_key in team_positions:
            # 使用该队伍的第一个出现位置
            start_idx, start_col = team_positions[team_key][0]
            players = parse_players_from_position(data, start_idx, start_col, team_key)
            if players:
                teams[team_key] = {
                    'name': f'队伍{team_key}',
                    'players': players
                }
    
    return teams

def parse_players_from_position(data, start_idx, start_col, team):
    """从指定位置开始解析选手数据"""
    players = []
    current_player = {}
    
    # 从队伍标识的下一行开始
    for idx in range(start_idx + 1, len(data)):
        row = data.iloc[idx]
        
        # 检查是否到达下一个队伍或数据结束
        next_team_indicator = str(row[start_col]).strip()
        if next_team_indicator in ['A', 'B'] and next_team_indicator != team:
            break
        
        # 跳过空行
        if pd.isna(row[start_col]) or str(row[start_col]).strip() == '':
            continue
            
        # 查找选手姓名（通常在数据列左侧的列中）
        player_name = None
        for col_idx in range(max(0, data.columns.get_loc(start_col) - 3), data.columns.get_loc(start_col)):
            name_value = str(row.iloc[col_idx]).strip()
            if name_value and name_value != 'nan' and len(name_value) > 1 and name_value not in ['A', 'B']:
                player_name = name_value
                break
        
        # 如果找到选手姓名，开始新选手的数据
        if player_name:
            # 保存上一个选手的数据
            if current_player and 'name' in current_player:
                players.append(current_player)
            
            # 开始新选手
            current_player = {'name': player_name}
            
            # 解析该行的统计数据
            for col in data.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip():
                    stat_name = str(col).strip()
                    if '击杀' in stat_name:
                        current_player['kills'] = int(value) if str(value).isdigit() else 0
                    elif '死亡' in stat_name:
                        current_player['deaths'] = int(value) if str(value).isdigit() else 0
                    elif '助攻' in stat_name:
                        current_player['assists'] = int(value) if str(value).isdigit() else 0
                    elif '爆头' in stat_name:
                        current_player['headshots'] = int(value) if str(value).isdigit() else 0
                    elif '首杀' in stat_name:
                        current_player['first_kills'] = int(value) if str(value).isdigit() else 0
    
    # 添加最后一个选手
    if current_player and 'name' in current_player:
        players.append(current_player)
    
    return players

def parse_players_from_column(data, data_column, team):
    """从指定列解析选手数据"""
    players = []
    
    # 找到数据开始行
    start_row = 0
    for idx, row in data.iterrows():
        if str(row[data_column]).strip() == team:
            start_row = idx
            break
    
    if start_row == 0:
        return players
    
    # 解析选手数据
    current_player = {}
    for idx in range(start_row + 1, len(data)):
        row = data.iloc[idx]
        player_name = str(row[data_column]).strip()
        
        if not player_name or player_name == 'nan':
            # 如果当前有选手数据，保存它
            if current_player and 'name' in current_player:
                players.append(current_player)
            current_player = {}
            continue
        
        # 检查是否是新的选手开始
        if idx > start_row + 1:
            # 查找选手姓名（通常在前面几列）
            for col in data.columns:
                name_value = str(row[col]).strip()
                if name_value and name_value != 'nan' and len(name_value) > 1:
                    current_player['name'] = name_value
                    break
        
        # 解析其他统计数据
        for col in data.columns:
            if col != data_column:
                value = row[col]
                if pd.notna(value) and str(value).strip():
                    stat_name = str(col).strip()
                    if '击杀' in stat_name:
                        current_player['kills'] = int(value) if str(value).isdigit() else 0
                    elif '死亡' in stat_name:
                        current_player['deaths'] = int(value) if str(value).isdigit() else 0
                    elif '助攻' in stat_name:
                        current_player['assists'] = int(value) if str(value).isdigit() else 0
                    elif '爆头' in stat_name:
                        current_player['headshots'] = int(value) if str(value).isdigit() else 0
                    elif '首杀' in stat_name:
                        current_player['first_kills'] = int(value) if str(value).isdigit() else 0
    
    # 添加最后一个选手
    if current_player and 'name' in current_player:
        players.append(current_player)
    
    return players

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """获取所有比赛"""
    matches = Match.query.order_by(Match.date.desc()).all()
    matches_list = []
    
    for match in matches:
        matches_list.append({
            'id': match.id,
            'name': match.name,
            'map': match.map,
            'date': match.date.strftime('%Y-%m-%d %H:%M'),
            'team_a_name': match.team_a_name,
            'team_b_name': match.team_b_name,
            'team_a_score': match.team_a_score,
            'team_b_score': match.team_b_score,
            'file_path': match.file_path
        })
    
    return jsonify(matches_list)

@app.route('/api/matches/<int:match_id>', methods=['GET'])
def get_match_detail(match_id):
    """获取比赛详情"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404
    
    players = PlayerMatch.query.filter_by(match_id=match_id).all()
    
    match_data = {
        'id': match.id,
        'name': match.name,
        'map': match.map,
        'date': match.date.strftime('%Y-%m-%d %H:%M'),
        'teams': {
            'A': {
                'name': match.team_a_name,
                'score': match.team_a_score,
                'players': []
            },
            'B': {
                'name': match.team_b_name,
                'score': match.team_b_score,
                'players': []
            }
        }
    }
    
    for player_match in players:
        player = player_match.player
        player_data = {
            'name': player.name,
            'kills': player_match.kills,
            'deaths': player_match.deaths,
            'assists': player_match.assists,
            'headshots': player_match.headshots,
            'first_kills': player_match.first_kills,
            'kd_ratio': round(player_match.kills / max(player_match.deaths, 1), 2)
        }
        
        team_key = 'A' if player_match.team == 'A' else 'B'
        match_data['teams'][team_key]['players'].append(player_data)
    
    return jsonify(match_data)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传Excel文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 解析Excel数据
        parsed_data = parse_excel_data(file_path)
        if not parsed_data:
            return jsonify({'error': '文件解析失败'}), 400
        
        # 保存到数据库
        try:
            # 提取队伍信息
            team_data = parsed_data['team_data']
            team_a_info = team_data.get('A', {})
            team_b_info = team_data.get('B', {})
            
            match = Match(
                name=parsed_data['match_info']['name'],
                map=parsed_data['match_info']['map'],
                date=datetime.now(),
                file_path=file_path,
                team_a_name=team_a_info.get('name', '队伍A'),
                team_b_name=team_b_info.get('name', '队伍B'),
                team_a_score=int(team_a_info.get('score', 0)) if team_a_info.get('score', '').isdigit() else 0,
                team_b_score=int(team_b_info.get('score', 0)) if team_b_info.get('score', '').isdigit() else 0
            )
            db.session.add(match)
            db.session.flush()  # 获取match.id
            
            # 保存选手数据
            for team_key, team_data in parsed_data['team_data'].items():
                for player_data in team_data['players']:
                    # 查找或创建选手
                    player = Player.query.filter_by(name=player_data['name']).first()
                    if not player:
                        player = Player(name=player_data['name'])
                        db.session.add(player)
                        db.session.flush()
                    
                    # 创建选手比赛记录
                    player_match = PlayerMatch(
                        player_id=player.id,
                        match_id=match.id,
                        team=team_key,
                        kills=player_data.get('kills', 0),
                        deaths=player_data.get('deaths', 0),
                        assists=player_data.get('assists', 0),
                        headshots=player_data.get('headshots', 0),
                        first_kills=player_data.get('first_kills', 0),
                        rws=player_data.get('rws', 0.0),
                        rating=player_data.get('rating', 0.0),
                        rating_plus=player_data.get('rating_plus', 0.0),
                        adr=player_data.get('adr', 0.0),
                        headshot_rate=player_data.get('headshot_rate', 0.0),
                        kast=player_data.get('kast', 0.0),
                        sniper_kills=player_data.get('sniper_kills', 0),
                        first_deaths=player_data.get('first_deaths', 0)
                    )
                    db.session.add(player_match)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '文件上传成功',
                'match_id': match.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'数据保存失败: {str(e)}'}), 500
    
    return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/api/matches/<int:match_id>', methods=['DELETE'])
def delete_match(match_id):
    """删除比赛"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404
    
    try:
        # 删除相关数据
        PlayerMatch.query.filter_by(match_id=match_id).delete()
        db.session.delete(match)
        db.session.commit()
        
        # 删除文件
        if os.path.exists(match.file_path):
            os.remove(match.file_path)
        
        return jsonify({'success': True, 'message': '比赛删除成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

def calculate_players_data():
    """计算所有选手的统计数据（不筛选）"""
    # 获取所有选手的比赛数据
    players_data = {}
    
    # 查询所有选手的比赛记录
    player_matches = PlayerMatch.query.all()
    
    for pm in player_matches:
        player_name = pm.player.name
        
        if player_name not in players_data:
            players_data[player_name] = {
                'name': player_name,
                'totalKills': 0,
                'totalDeaths': 0,
                'totalAssists': 0,
                'totalHeadshots': 0,
                'totalFirstKills': 0,
                'totalFirstDeaths': 0,
                'totalMatches': 0,
                'totalRatingPlus': 0.0,
                'totalADR': 0.0,
                'totalRWS': 0.0,
                'totalKAST': 0.0,
                'totalSniperKills': 0
            }
        
        players_data[player_name]['totalKills'] += pm.kills
        players_data[player_name]['totalDeaths'] += pm.deaths
        players_data[player_name]['totalAssists'] += pm.assists
        players_data[player_name]['totalHeadshots'] += pm.headshots
        players_data[player_name]['totalFirstKills'] += pm.first_kills
        players_data[player_name]['totalFirstDeaths'] += pm.first_deaths
        players_data[player_name]['totalRatingPlus'] += pm.rating_plus
        players_data[player_name]['totalADR'] += pm.adr
        players_data[player_name]['totalRWS'] += pm.rws
        players_data[player_name]['totalKAST'] += pm.kast
        players_data[player_name]['totalSniperKills'] += pm.sniper_kills
        players_data[player_name]['totalMatches'] += 1
    
    # 转换为数组并计算统计数据
    players_array = []
    for player_name, data in players_data.items():
        player_info = {
            'name': player_name,
            'totalKills': data['totalKills'],
            'totalDeaths': data['totalDeaths'],
            'totalAssists': data['totalAssists'],
            'totalHeadshots': data['totalHeadshots'],
            'totalFirstKills': data['totalFirstKills'],
            'totalFirstDeaths': data['totalFirstDeaths'],
            'totalRatingPlus': data['totalRatingPlus'],
            'totalADR': data['totalADR'],
            'totalRWS': data['totalRWS'],
            'totalKAST': data['totalKAST'],
            'totalSniperKills': data['totalSniperKills'],
            'totalMatches': data['totalMatches']
        }
        
        # 计算衍生数据
        player_info['kdRatio'] = round(data['totalKills'] / max(data['totalDeaths'], 1), 2)
        player_info['avgKills'] = round(data['totalKills'] / data['totalMatches'], 1)
        player_info['avgDeaths'] = round(data['totalDeaths'] / data['totalMatches'], 1)
        player_info['avgAssists'] = round(data['totalAssists'] / data['totalMatches'], 1)
        player_info['avgHeadshots'] = round(data['totalHeadshots'] / data['totalMatches'], 1)
        player_info['avgFirstKills'] = round(data['totalFirstKills'] / data['totalMatches'], 1)
        player_info['avgFirstDeaths'] = round(data['totalFirstDeaths'] / data['totalMatches'], 1)
        player_info['avgRatingPlus'] = round(data['totalRatingPlus'] / data['totalMatches'], 2)
        player_info['avgADR'] = round(data['totalADR'] / data['totalMatches'], 1)
        player_info['avgRWS'] = round(data['totalRWS'] / data['totalMatches'], 1)
        player_info['avgKAST'] = round(data['totalKAST'] / data['totalMatches'], 1)
        player_info['headshotRatio'] = round(data['totalHeadshots'] / max(data['totalKills'], 1) * 100, 1)
        player_info['avgsniperkills'] = round(data['totalSniperKills'] / max(data['totalKills'], 1) * 100, 1)
        players_array.append(player_info)
    
    # 按姓名排序
    players_array.sort(key=lambda x: x['name'])
    
    return players_array

@app.route('/api/players', methods=['GET'])
def get_players():
    """获取所有选手的统计数据（不筛选）"""
    players_array = calculate_players_data()
    return jsonify(players_array)

@app.route('/api/leaderboards', methods=['GET'])
def get_leaderboards():
    """获取所有榜单数据"""
    players_array = calculate_players_data()
    
    # 计算各种榜单
    leaderboards = {
        'mvp': calculate_mvp_leaderboard(players_array),
        'headshot_maniac': calculate_headshot_maniac_leaderboard(players_array),
        'first_kill_assassin': calculate_first_kill_assassin_leaderboard(players_array),
        'immortal_warrior': calculate_immortal_warrior_leaderboard(players_array),
        'team_glue': calculate_team_glue_leaderboard(players_array),
        'sniper_god': calculate_sniper_god_leaderboard(players_array),
        'economic_destroyer': calculate_economic_destroyer_leaderboard(players_array),
        'adversity_hero': calculate_adversity_hero_leaderboard(players_array),
        'steady_player': calculate_steady_player_leaderboard(players_array),
        'high_risk_high_reward': calculate_high_risk_high_reward_leaderboard(players_array),
        'no_free_wins': calculate_no_free_wins_leaderboard(players_array),
        'rws_dominance': calculate_rws_dominance_leaderboard(players_array)
    }
    
    return jsonify(leaderboards)

def calculate_mvp_leaderboard(players):
    """计算MVP榜单（按平均Rating+降序排列）"""
    mvp_leaderboard = []
    
    for player in players:
        # 筛选条件：至少1场比赛且Rating+ ≥ 1.0
        if player['totalMatches'] >= 1 and player['avgRatingPlus'] >= 1.0:
            mvp_leaderboard.append({
                'name': player['name'],
                'score': player['avgRatingPlus'],
                'avgRatingPlus': player['avgRatingPlus'],
                'totalMatches': player['totalMatches'],
                'tag': '🏆【官方认证】'
            })
    
    # 排序
    sorted_leaderboard = sorted(mvp_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard

def calculate_headshot_maniac_leaderboard(players):
    """计算爆头狂魔榜（按平均爆头率降序排列）"""
    headshot_maniac_leaderboard = []
    
    for player in players:
        # 筛选条件：爆头率 ≥ 40% 且场均击杀 ≥ 10
        tag = ''
        if player['headshotRatio'] >= 60 and player['avgKills'] >= 10:
            tag = '🔥【kuku爆头开了】'
        elif player['headshotRatio'] >= 50 and player['avgKills'] >= 10:
            tag = '💀【颅骨粉碎者】'
        else:
            tag = ''
        if player['headshotRatio'] >= 40 and player['avgKills'] >= 10:
            headshot_maniac_leaderboard.append({
                'name': player['name'],
                'score': player['headshotRatio'],
                'headshotRatio': player['headshotRatio'],
                'avgKills': player['avgKills'],
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(headshot_maniac_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard

def calculate_first_kill_assassin_leaderboard(players):
    """计算突破刺客榜（按突破效率指数EI降序排列）"""
    breakthrough_assassin_leaderboard = []
    
    for player in players:
        # 计算突破效率指数EI
        avg_first_kills = player['avgFirstKills']
        avg_first_deaths = player['avgFirstDeaths']
        avg_kd = player['kdRatio']
        avg_adr = player['avgADR']
        avg_kast = player['avgKAST']
        
        # 首杀成功率 = 平均首杀数 / (平均首杀数 + 平均首死数)
        first_kill_success_rate = avg_first_kills / (avg_first_kills + avg_first_deaths + 0.1)
        
        # EI = (平均首杀数 × 首杀成功率^1.3) × (1 + (平均K/D - 1) / 3) × (1 - 平均首死数 / (平均首杀数 + 平均首死数 + 0.1)) × min(1.0, 平均ADR / 80)
        ei = (avg_first_kills * (first_kill_success_rate ** 1.3)) * \
             (1 + (avg_kd - 1) / 3) * \
             (1 - avg_first_deaths / (avg_first_kills + avg_first_deaths + 0.1)) * \
             min(1.0, avg_adr / 80)
        
        # 确定特效标签
        tag = ''
        if ei >= 0.8 and first_kill_success_rate >= 0.5:
            tag = '💥【破门专家】'
        elif avg_first_kills >= 0.7 and first_kill_success_rate < 0.4:
            tag = '☠️【烈士型先锋】'
        elif ei >= 0.7 and avg_kast >= 75:
            tag = '🔄【全能突破手】'
        elif first_kill_success_rate >= 0.55 and avg_adr >= 85:
            tag = '🎯【高效尖刀】'
        elif avg_first_deaths > avg_first_kills and avg_kd < 0.9:
            tag = '🛑【伪突破手】'
        else:
            tag = '🔪【突破手】'
        
        # 筛选条件：总场次 ≥ 1 且有基本的首杀数据
        if player['totalMatches'] >= 1 and (ei >0.3):
            breakthrough_assassin_leaderboard.append({
                'name': player['name'],
                'score': round(ei, 2),
                'ei': round(ei, 2),
                'avgFirstKills': avg_first_kills,
                'avgFirstDeaths': avg_first_deaths,
                'firstKillSuccessRate': round(first_kill_success_rate * 100, 1),
                'avgKD': round(avg_kd, 2),
                'avgADR': round(avg_adr, 1),
                'avgKAST': round(avg_kast, 1),
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(breakthrough_assassin_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard

def calculate_immortal_warrior_leaderboard(players):
    """计算生存榜（按survival_score降序排列）"""
    immortal_warrior_leaderboard = []
    
    for player in players:
        # 计算生存分数：综合考虑死亡数、KAST和Rating+
        # 公式：生存分数 = (25 - 平均死亡数) * KAST * Rating+ / 25
        base_survival = max(0, 25 - player['avgDeaths'])
        survival_score = (base_survival / 25) * player['avgKAST'] * min(2.0, player['avgRatingPlus'])
        
        # 确定特效标签
        tag = ''
        if player['avgDeaths'] <= 12 and player['avgKAST'] >= 0.7 and player['avgRatingPlus'] >= 1.2:
            tag = '🛡️【钢铁意志】'
        elif player['avgDeaths'] <= 15 and player['avgKAST'] >= 0.75 and player['avgRatingPlus'] >= 1.0:
            tag = '🎯【高效生存者】'
        elif player['avgDeaths'] >= 18 and player['avgKAST'] >= 0.7:
            tag = '☠️【送头王】'
        elif player['avgKAST'] >= 0.65 and player['avgRatingPlus'] < 0.95:
            tag = '🐢【龟甲战神】'
        elif player['avgDeaths'] <= 10 and player['kdRatio'] >= 1.5:
            tag = '⚔️【生存大师】'
        else:
            tag = '🔰【普通生存者】'
        
        # 筛选条件：场均死亡 ≤ 20 且有一定KAST贡献
        if player['avgDeaths'] <= 20 and player['avgKAST'] >= 0.6:
            immortal_warrior_leaderboard.append({
                'name': player['name'],
                'score': round(survival_score, 2),
                'survival_score': round(survival_score, 2),
                'avgDeaths': player['avgDeaths'],
                'kdRatio': round(player['kdRatio'], 2),
                'avgKAST': round(player['avgKAST'] * 100, 1),
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(immortal_warrior_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard

def calculate_team_glue_leaderboard(players):
    """计算团队粘合剂榜（按平均KAST降序排列）"""
    team_glue_leaderboard = []
    
    for player in players:
        # 筛选条件：KAST ≥ 65% 且助攻 ≥ 2（降低KAST要求）
        tag = ''
        if player['avgKAST'] >= 0.65 and player['avgAssists'] >= 2:
            tag = '🤝【节奏引擎】'
        else:
            tag = ''
        if player['avgKAST'] >= 0.55 and player['avgAssists'] >= 2:
            team_glue_leaderboard.append({
                'name': player['name'],
                'score': player['avgKAST'],
                'avgKAST': player['avgKAST'],
                'avgAssists': player['avgAssists'],
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(team_glue_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard

def calculate_sniper_god_leaderboard(players):
    """计算狙神天梯榜（按平均狙杀数×(平均爆头率/100)加权狙杀效率降序）"""
    sniper_god_leaderboard = []
    
    for player in players:
        # 计算狙神分数
        # 由于没有狙击枪回合占比数据，简化为仅使用狙杀数
        sniper_score = player['avgsniperkills'] * (player['headshotRatio'] / 100)
        tag = ''
        if player['avgsniperkills'] >=8 and player['headshotRatio'] >= 40:
            tag = '🎯【千里夺命】'
        else:
            tag = ''
        # 筛选条件：场均狙杀 ≥ 2 且使用狙击枪回合占比 ≥ 30%（简化为狙杀数）
        if player['avgsniperkills'] >= 5:
            sniper_god_leaderboard.append({
                'name': player['name'],
                'score': round(sniper_score, 2),
                'avgHeadshots': player['avgHeadshots'],
                'headshotRatio': player['headshotRatio'],
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(sniper_god_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard

def calculate_economic_destroyer_leaderboard(players):
    """计算经济破坏王榜（按平均ADR降序排列）"""
    economic_destroyer_leaderboard = []
    
    for player in players:
        # 筛选条件：ADR ≥ 85 且 Rating+ ≥ 1.0
        tag = ''
        if player['avgADR'] >= 110 and player['avgRatingPlus'] >= 1.0:
            tag = '💥【一键扫荡】'
        elif player['avgADR'] >= 95 and player['avgRatingPlus'] >= 1.0:
            tag = '💸【弹药富翁】'
        else:
            tag = ''
        if player['avgADR'] >= 85 and player['avgRatingPlus'] >= 1.0:
            economic_destroyer_leaderboard.append({
                'name': player['name'],
                'score': player['avgADR'],
                'avgADR': player['avgADR'],
                'avgRatingPlus': player['avgRatingPlus'],
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(economic_destroyer_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard


def calculate_steady_player_leaderboard(players):
    """计算稳定如狗榜（按Rating+标准差升序排列）"""
    # 注意：由于我们没有单场比赛的Rating+数据，无法计算标准差
    # 这里简化为使用平均Rating+的稳定性，实际应用中需要修改数据收集逻辑
    steady_player_leaderboard = []
    
    for player in players:
        # 确定特效标签
        if player['avgRatingPlus'] >= 1.3:
            tag = '🔪【超级主C】'
        elif player['avgRatingPlus'] >= 1.1:
            tag = '📊【人形自走AI】'
        else:
            tag = ''
            
        # 筛选条件：平均Rating+ ≥ 0.85（简化实现）
        if player['avgRatingPlus'] >= 1:
            steady_player_leaderboard.append({
                'name': player['name'],
                'score': player['avgRatingPlus'],
                'avgRatingPlus': player['avgRatingPlus'],
                'tag': tag
            })
    
    # 排序（由于无法计算标准差，这里按平均Rating+降序排列）
    sorted_leaderboard = sorted(steady_player_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard


def calculate_high_risk_high_reward_leaderboard(players):
    """计算击杀效率榜（按KES降序排列）"""
    high_risk_high_reward_leaderboard = []
    
    for player in players:
        # 计算击杀效率分数KES
        # KES = (平均击杀 × ADR / 80) × min(1.2, 平均K/D) × (平均Rating+ / 1.0) × (平均RWS)
        kes = (player['avgKills'] * player['avgADR'] / 80) * \
              min(1, player['kdRatio']) * \
              (player['avgRatingPlus'] / 1.0) * \
              (player['avgRWS']/500)
        
        # 确定特效标签
        tag = ''
        if kes >= 1.8 and player['avgADR'] >= 85:
            tag = '⚡【高效收割者】'
        elif player['avgKills'] >= 20 and kes < 1.2:
            tag = '💥【暴力输出机】'
        elif kes >= 1.6 and player['kdRatio'] >= 1.1:
            tag = '🎯【精英杀手】'
        elif player['avgKills'] >= 18:
            tag = '🚫【数据泡沫】'
        else:
            tag = '🔰【普通杀手】'
        
        # 进榜条件：平均击杀 ≥ 12
        if player['avgKills'] >= 12:
            high_risk_high_reward_leaderboard.append({
                'name': player['name'],
                'score': round(kes, 2),
                'kes': round(kes, 2),
                'avgKills': player['avgKills'],
                'avgADR': round(player['avgADR'], 1),
                'kdRatio': round(player['kdRatio'], 2),
                'avgRatingPlus': round(player['avgRatingPlus'], 2),
                'avgRWS': round(player['avgRWS'], 1),
                'tag': tag
            })
    
    # 排序
    sorted_leaderboard = sorted(high_risk_high_reward_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard


def calculate_no_free_wins_leaderboard(players):
    """计算躺赢绝缘体榜（按胜场中个人Rating+与队伍平均Rating+的差值降序）"""
    # 注意：由于我们没有队伍级别的数据，无法计算队伍平均Rating+
    # 这里简化为使用个人平均Rating+，实际应用中需要修改数据收集逻辑
    no_free_wins_leaderboard = []
    
    for player in players:
        # 筛选条件：平均Rating+ ≥ 1.0（简化实现）
        if player['avgRatingPlus'] >= 1.0 and player['avgKAST'] >= 0.63 and player["avgRWS"] >= 10:
            no_free_wins_leaderboard.append({
                'name': player['name'],
                'score': player['avgRatingPlus'],
                'avgRatingPlus': player['avgRatingPlus'],
                'tag': '🚫【从不混子】'
            })
    
    # 排序（由于无法计算差值，这里按平均Rating+降序排列）
    sorted_leaderboard = sorted(no_free_wins_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard


def calculate_rws_dominance_leaderboard(players):
    """计算RWS统治力榜（按平均RWS降序排列）"""
    rws_dominance_leaderboard = []
    
    for player in players:
        # 筛选条件：RWS ≥ 12（根据榜单描述）
        if player['avgRWS'] >= 12:
            rws_dominance_leaderboard.append({
                'name': player['name'],
                'score': player['avgRWS'],
                'avgRWS': player['avgRWS'],
                'tag': '👑【残局之神】'
            })
    
    # 排序
    sorted_leaderboard = sorted(rws_dominance_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard


def calculate_adversity_hero_leaderboard(players):
    """计算逆境英雄榜（在选手败场中，按败场中的平均Rating+降序）"""
    # 注意：由于我们没有记录每场比赛的胜负情况，无法准确计算败场中的平均Rating+
    # 这里简化为使用所有比赛的平均Rating+，实际应用中需要修改数据收集逻辑
    adversity_hero_leaderboard = []
    
    # 查询所有选手的比赛记录，统计败场数据
    player_matches = PlayerMatch.query.all()
    loss_data = {}
    
    for pm in player_matches:
        player_name = pm.player.name
        match = pm.match
        
        # 确定选手所在队伍是否失败
        player_team = pm.team
        team_a_win = match.team_a_score > match.team_b_score
        is_loss = (player_team == 'A' and not team_a_win) or (player_team == 'B' and team_a_win)
        
        if is_loss:
            if player_name not in loss_data:
                loss_data[player_name] = {
                    'totalRatingPlus': 0.0,
                    'totalLossMatches': 0
                }
            loss_data[player_name]['totalRatingPlus'] += pm.rating_plus
            loss_data[player_name]['totalLossMatches'] += 1
    
    for player in players:
        player_name = player['name']
        
        # 检查该选手是否有败场记录
        if player_name in loss_data and loss_data[player_name]['totalLossMatches'] >= 1:
            avg_loss_rating_plus = loss_data[player_name]['totalRatingPlus'] / loss_data[player_name]['totalLossMatches']
            
            # 筛选条件：至少参与1场败局，且败场Rating+ ≥ 1.1
            if avg_loss_rating_plus >= 1.1:
                adversity_hero_leaderboard.append({
                    'name': player_name,
                    'score': round(avg_loss_rating_plus, 2),
                    'avgLossRatingPlus': round(avg_loss_rating_plus, 2),
                    'totalLossMatches': loss_data[player_name]['totalLossMatches'],
                    'tag': '🌪️【孤胆救世主】'
                })
    
    # 排序
    sorted_leaderboard = sorted(adversity_hero_leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    
    return sorted_leaderboard


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)