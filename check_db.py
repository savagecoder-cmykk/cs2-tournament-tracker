from app import app, db
from models import Match, Player, PlayerMatch

with app.app_context():
    print('数据库表结构:', db.metadata.tables.keys())
    print('Match记录数:', Match.query.count())
    print('Player记录数:', Player.query.count())
    print('PlayerMatch记录数:', PlayerMatch.query.count())
    
    savage = Player.query.filter_by(name='savage').first()
    if savage:
        print('savage的比赛数:', len(savage.matches))
        print('savage的PlayerMatch记录:', PlayerMatch.query.filter_by(player_id=savage.id).count())
    else:
        print('savage未找到')
