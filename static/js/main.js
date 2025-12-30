// CS2 赛事追踪系统 - JavaScript 主文件

// 全局变量
let matches = [];
let selectedMatch = null;
let currentTab = 'match-history';
let currentSubTab = 'player-data';

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    loadMatches();
    setupEventListeners();
});

// 初始化页面
function initializePage() {
    // 设置默认显示
    showTab('match-history');
}

// 加载比赛数据
async function loadMatches() {
    try {
        const response = await fetch('/api/matches');
        matches = await response.json();
        renderMatchList();
    } catch (error) {
        console.error('加载比赛数据失败:', error);
        showNotification('加载比赛数据失败', 'error');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 主标签页切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.target.getAttribute('data-tab');
            showTab(tabName);
        });
    });

    // 子标签页切换
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const subTabName = e.target.getAttribute('data-subtab');
            showSubTab(subTabName);
        });
    });

    // 文件上传
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
}

// 显示标签页
function showTab(tabName) {
    // 隐藏所有标签页
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的标签页
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    currentTab = tabName;

    // 处理子标签页显示
    if (tabName === 'data-dashboard') {
        document.getElementById('subTabNavContainer').style.display = 'block';
        showSubTab('player-data');
    } else {
        document.getElementById('subTabNavContainer').style.display = 'none';
    }
}

// 显示子标签页
function showSubTab(subTabName) {
    // 隐藏所有子标签页
    document.querySelectorAll('.sub-tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的子标签页
    document.getElementById(subTabName).classList.add('active');
    document.querySelector(`[data-subtab="${subTabName}"]`).classList.add('active');

    currentSubTab = subTabName;

    // 加载对应内容
    if (subTabName === 'player-data') {
        renderPlayerData();
    } else if (subTabName === 'leaderboards') {
        renderLeaderboards();
    }
}

// 渲染比赛列表
function renderMatchList() {
    const container = document.getElementById('matchesContainer');
    container.innerHTML = '';

    if (matches.length === 0) {
        container.innerHTML = '<div class="no-data">暂无比赛记录</div>';
        return;
    }

    matches.forEach((match, index) => {
        const card = document.createElement('div');
        card.className = `match-card ${selectedMatch === index ? 'active' : ''}`;
        card.innerHTML = `
            <div class="match-name">${match.name}</div>
            <div class="match-map">
                <i class="fas fa-map-marker-alt"></i>
                ${match.map}
            </div>
            <button class="delete-btn" onclick="deleteMatch(${match.id})">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        card.addEventListener('click', () => selectMatch(index));
        container.appendChild(card);
    });
}

// 选择比赛
async function selectMatch(index) {
    selectedMatch = index;
    renderMatchList();
    
    try {
        const match = matches[index];
        const response = await fetch(`/api/matches/${match.id}`);
        const matchDetails = await response.json();
        renderMatchDetails(matchDetails);
    } catch (error) {
        console.error('加载比赛详情失败:', error);
        showNotification('加载比赛详情失败', 'error');
    }
}

// 渲染比赛详情
function renderMatchDetails(match) {
    const container = document.getElementById('matchDetails');
    
    if (!match) {
        container.innerHTML = '<div class="no-match-selected"><i class="fas fa-info-circle"></i> 请选择一个比赛查看详情</div>';
        return;
    }

    // 使用实际比赛得分，而不是选手击杀数之和
    const teamAScore = match.teams.A.score || 0;
    const teamBScore = match.teams.B.score || 0;

    container.innerHTML = `
        <div class="match-header">
            <div class="match-info">
                <div class="match-result">
                    <div class="team-result">
                        <div class="team-name">${match.teams.A.name}</div>
                        <div class="team-score">${teamAScore}</div>
                    </div>
                    <div style="font-size: 20px; color: #888;">vs</div>
                    <div class="team-result">
                        <div class="team-score">${teamBScore}</div>
                        <div class="team-name">${match.teams.B.name}</div>
                    </div>
                </div>
                <div class="game-info">
                    <div class="info-item">
                        <i class="fas fa-map"></i>
                        <span>${match.map}</span>
                    </div>
                    <div class="info-item">
                        <i class="fas fa-calendar"></i>
                        <span>${match.date}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="players-container">
            <div class="team-section">
                <div class="team-title">${match.teams.A.name}</div>
                <div id="teamAPlayers"></div>
            </div>
            <div class="team-section">
                <div class="team-title">${match.teams.B.name}</div>
                <div id="teamBPlayers"></div>
            </div>
        </div>
    `;

    // 渲染选手列表
    renderPlayers('teamAPlayers', match.teams.A.players);
    renderPlayers('teamBPlayers', match.teams.B.players);
}

// 渲染选手列表
function renderPlayers(containerId, players) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    players.forEach((player, index) => {
        const playerCard = document.createElement('div');
        playerCard.className = 'player-card';
        playerCard.innerHTML = `
            <div class="player-main-info">
                <div class="player-avatar">${player.name.charAt(0)}</div>
                <div class="player-name">${player.name}</div>
            </div>
            <div class="player-stats">
                <div class="stat-item kda">
                    <div class="stat-value">${player.kills}/${player.deaths}/${player.assists}</div>
                    <div class="stat-label">K/D/A</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${player.kd_ratio}</div>
                    <div class="stat-label">K/D</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${player.headshots}</div>
                    <div class="stat-label">爆头</div>
                </div>
            </div>
        `;

        // 添加点击展开详情功能
        playerCard.addEventListener('click', () => {
            if (playerCard.classList.contains('expanded')) {
                playerCard.classList.remove('expanded');
                const details = playerCard.querySelector('.player-details');
                if (details) details.remove();
            } else {
                playerCard.classList.add('expanded');
                const details = document.createElement('div');
                details.className = 'player-details';
                details.innerHTML = `
                    <div class="detail-item">
                        <div class="detail-value">${player.kills}</div>
                        <div class="detail-label">总击杀</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${player.deaths}</div>
                        <div class="detail-label">总死亡</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${player.headshots}</div>
                        <div class="detail-label">爆头击杀</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">${player.first_kills}</div>
                        <div class="detail-label">首杀</div>
                    </div>
                `;
                playerCard.appendChild(details);
            }
        });

        container.appendChild(playerCard);
    });
}

// 删除比赛
async function deleteMatch(matchId) {
    if (!confirm('确定要删除这个比赛记录吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/matches/${matchId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('比赛记录删除成功', 'success');
            selectedMatch = null;
            loadMatches();
            renderMatchDetails(null);
        } else {
            showNotification('删除比赛记录失败', 'error');
        }
    } catch (error) {
        console.error('删除比赛失败:', error);
        showNotification('删除比赛记录失败', 'error');
    }
}

// 处理文件上传
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 验证文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showNotification('请上传Excel文件（.xlsx或.xls格式）！', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('比赛记录上传成功！', 'success');
            loadMatches();
        } else {
            showNotification(result.error || '文件上传失败', 'error');
        }
    } catch (error) {
        console.error('文件上传失败:', error);
        showNotification('文件上传失败', 'error');
    }

    // 清空文件输入
    event.target.value = '';
}

// 渲染选手数据
async function renderPlayerData() {
    const container = document.getElementById('playerStatsTable');
    
    try {
        const response = await fetch('/api/players');
        const playersData = await response.json();
        
        if (playersData.length === 0) {
            container.innerHTML = '<div class="no-data">暂无选手数据</div>';
            return;
        }

        // 创建表格
        let tableHTML = `
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>选手</th>
                        <th>比赛场次</th>
                        <th>平均击杀</th>
                        <th>平均死亡</th>
                        <th>平均K/D</th>
                        <th>平均助攻</th>
                        <th>平均爆头率(%)</th>
                        <th>平均首杀数</th>
                        <th>平均Rating+</th>
                        <th>平均ADR</th>
                        <th>平均RWS</th>
                        <th>平均KAST</th>
                    </tr>
                </thead>
                <tbody>
        `;

        // 添加选手数据行
        playersData.forEach(player => {
            tableHTML += `
                <tr>
                    <td><strong>${player.name}</strong></td>
                    <td>${player.totalMatches || 0}</td>
                    <td>${player.avgKills || 0}</td>
                    <td>${player.avgDeaths || 0}</td>
                    <td>${player.kdRatio || '0.00'}</td>
                    <td>${player.avgAssists || 0}</td>
                    <td>${player.headshotRatio || 0}%</td>
                    <td>${player.avgFirstKills || 0}</td>
                    <td>${player.avgRatingPlus || 0.00}</td>
                    <td>${player.avgADR || 0}</td>
                    <td>${player.avgRWS || 0}</td>
                    <td>${player.avgKAST || 0}%</td>
                </tr>
            `;
        });

        tableHTML += '</tbody></table>';
        container.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('加载选手数据失败:', error);
        container.innerHTML = '<div class="error">加载选手数据失败</div>';
    }
}

// 渲染榜单
async function renderLeaderboards() {
    const container = document.getElementById('leaderboardsContent');
    
    try {
        const response = await fetch('/api/leaderboards');
        const leaderboards = await response.json();
        
        container.innerHTML = `
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>MVP榜</span>
                    <span class="metric-desc">按平均Rating+降序排列</span>
                </div>
                ${renderMvpLeaderboard(leaderboards.mvp)}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>爆头狂魔榜</span>
                    <span class="metric-desc">总和爆头率及有效击杀率</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.headshot_maniac, 'headshotRatio', 'avgKills', '%', '击杀')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>突破刺客榜</span>
                    <span class="metric-desc">综合平均首杀数、首杀成功率和平均首死数</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.first_kill_assassin, 'netFirstKills', 'avgFirstKills', '', '首杀')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>生存榜</span>
                    <span class="metric-desc">高存活率 + 高影响力 = 真生存大师</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.immortal_warrior, 'kdRatio', 'avgDeaths', '', '死亡')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>团队粘合剂榜</span>
                    <span class="metric-desc">按平均KAST降序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.team_glue, 'avgKAST', 'avgAssists', '%', '助攻')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>狙神天梯榜</span>
                    <span class="metric-desc">按平均狙杀数×(平均爆头率/100)降序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.sniper_god, 'avgHeadshots', 'headshotRatio', '', '%')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>伤害输出王榜</span>
                    <span class="metric-desc">按平均ADR降序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.economic_destroyer, 'avgADR', 'avgRatingPlus', '', '')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>稳定如狗榜</span>
                    <span class="metric-desc">按Rating+标准差升序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.steady_player, 'avgRatingPlus', '', '', '')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>击杀效率榜</span>
                    <span class="metric-desc">用最少风险换取最多击杀总和RWS\Rating\ADR</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.high_risk_high_reward, 'kes', 'avgRatingPlus')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>躺赢绝缘体榜</span>
                    <span class="metric-desc">按胜场中个人Rating+与队伍平均Rating+差值降序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.no_free_wins, 'avgRatingPlus', '', '', '')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>逆境英雄榜</span>
                    <span class="metric-desc">在选手败场中，按败场中的平均Rating+降序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.adversity_hero, 'avgLossRatingPlus', 'totalLossMatches', '', '败场')}
            </div>
            
            <div class="leaderboard">
                <div class="leaderboard-title">
                    <span>RWS统治力榜</span>
                    <span class="metric-desc">按平均RWS降序排列</span>
                </div>
                ${renderGenericLeaderboard(leaderboards.rws_dominance, 'avgRWS', '', '', '')}
            </div>
        `;
        
    } catch (error) {
        console.error('加载榜单数据失败:', error);
        container.innerHTML = '<div class="error">加载榜单数据失败</div>';
    }
}

// 渲染MVP榜单
function renderMvpLeaderboard(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">暂无数据</div>';
    }

    let tableHTML = '<div class="leaderboard-rows">';
    
    data.forEach((player, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const isTop3 = index < 3;
        
        // 为前三名添加特殊标签
        let specialBadge = '';
        if (index === 0) {
            specialBadge = '<span class="badge" style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white;">TOP 1</span>';
        } else if (index === 1) {
            specialBadge = '<span class="badge" style="background: linear-gradient(45deg, #4ecdc4, #45b7d1); color: white;">TOP 2</span>';
        } else if (index === 2) {
            specialBadge = '<span class="badge" style="background: linear-gradient(45deg, #a8edea, #fed6e3); color: #333;">TOP 3</span>';
        }
        
        tableHTML += `
            <div class="leaderboard-row ${isTop3 ? 'top3' : ''}">
                <div class="rank ${rankClass}">${index + 1}</div>
                <div class="player-name">
                    ${player.name}
                    ${specialBadge}
                </div>
                <div class="score">${player.score}</div>
                <div class="metric">${player.kdRatio} (${player.avgKills})</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    return tableHTML;
}

// 渲染狙击手榜单
function renderSniperLeaderboard(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">暂无数据</div>';
    }

    let tableHTML = '<div class="leaderboard-rows">';
    
    data.forEach((player, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const isTop3 = index < 3;
        
        // 为前三名添加特殊标签
        let specialBadge = '';
        if (index < 3) {
            specialBadge = '<span class="badge elite-sniper">比simple厉害但不如ZywOo</span>';
        }
        
        tableHTML += `
            <div class="leaderboard-row ${isTop3 ? 'top3' : ''}">
                <div class="rank ${rankClass}">${index + 1}</div>
                <div class="player-name">
                    ${player.name}
                    ${specialBadge}
                </div>
                <div class="score">${player.score}</div>
                <div class="metric">${player.avgHeadshots} (${player.headshotRatio}%)</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    return tableHTML;
}

// 渲染生存大师榜单
function renderSurvivalLeaderboard(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">暂无数据</div>';
    }

    let tableHTML = '<div class="leaderboard-rows">';
    
    data.forEach((player, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const isTop3 = index < 3;
        
        // 为前三名添加特殊标签
        let specialBadge = '';
        if (index === 0) {
            specialBadge = '<span class="badge iron-man">钢铁侠</span>';
        } else if (index === 1) {
            specialBadge = '<span class="badge iron-man">生存专家</span>';
        } else if (index === 2) {
            specialBadge = '<span class="badge iron-man">坚韧战士</span>';
        }
        
        tableHTML += `
            <div class="leaderboard-row ${isTop3 ? 'top3' : ''}">
                <div class="rank ${rankClass}">${index + 1}</div>
                <div class="player-name">
                    ${player.name}
                    ${specialBadge}
                </div>
                <div class="score">${player.score}</div>
                <div class="metric">${player.kdRatio} (${player.totalDeaths})</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    return tableHTML;
}

// 渲染黑马爆发榜单
function renderBreakoutLeaderboard(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">暂无数据</div>';
    }

    let tableHTML = '<div class="leaderboard-rows">';
    
    data.forEach((player, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const isTop3 = index < 3;
        
        // 只有前三名可以有新星崛起标签
        let specialBadge = '';
        if (index === 0) {
            specialBadge = '<span class="badge breakout">新星崛起</span>';
        } else if (index === 1) {
            specialBadge = '<span class="badge breakout">潜力新星</span>';
        } else if (index === 2) {
            specialBadge = '<span class="badge breakout">未来之星</span>';
        }
        
        tableHTML += `
            <div class="leaderboard-row ${isTop3 ? 'top3' : ''}">
                <div class="rank ${rankClass}">${index + 1}</div>
                <div class="player-name">
                    ${player.name}
                    ${specialBadge}
                </div>
                <div class="score">${player.score}</div>
                <div class="metric">${player.avgKills} (${player.totalMatches})</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    return tableHTML;
}

// 渲染通用榜单
function renderGenericLeaderboard(data, primaryMetric, secondaryMetric, unit = '', metricLabel = '') {
    if (!data || data.length === 0) {
        return '<div class="no-data">暂无数据</div>';
    }

    let tableHTML = '<div class="leaderboard-rows">';
    
    data.forEach((player, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const isTop3 = index < 3;
        
        // 获取特效标签
        const tag = player.tag || '';
        
        // 构建指标显示
        let metricDisplay = '';
        if (primaryMetric && secondaryMetric) {
            metricDisplay = `${player[primaryMetric] || 0}${unit} (${player[secondaryMetric] || 0}${metricLabel})`;
        } else if (primaryMetric) {
            metricDisplay = `${player[primaryMetric] || 0}${unit}`;
        }
        
        tableHTML += `
            <div class="leaderboard-row ${isTop3 ? 'top3' : ''}">
                <div class="rank ${rankClass}">${index + 1}</div>
                <div class="player-name">
                    ${player.name}
                    ${tag ? `<span class="badge special-tag">${tag}</span>` : ''}
                </div>
                <div class="score">${player.score}</div>
                <div class="metric">${metricDisplay}</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    return tableHTML;
}

// 渲染爆头精英榜单
function renderHeadshotLeaderboard(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">暂无数据</div>';
    }

    let tableHTML = '<div class="leaderboard-rows">';
    
    data.forEach((player, index) => {
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const isTop3 = index < 3;
        
        // 为前三名添加特殊标签
        let specialBadge = '';
        if (index === 0) {
            specialBadge = '<span class="badge" style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white;">kuku打头开挂了</span>';
        } else if (index === 1) {
            specialBadge = '<span class="badge" style="background: linear-gradient(45deg, #4ecdc4, #45b7d1); color: white;">如开</span>';
        } else if (index === 2) {
            specialBadge = '<span class="badge" style="background: linear-gradient(45deg, #a8edea, #fed6e3); color: #333;">爆头侠</span>';
        }
        
        tableHTML += `
            <div class="leaderboard-row ${isTop3 ? 'top3' : ''}">
                <div class="rank ${rankClass}">${index + 1}</div>
                <div class="player-name">
                    ${player.name}
                    ${specialBadge}
                </div>
                <div class="score">${player.score}</div>
                <div class="metric">${player.avgHeadshots} (${player.headshotRatio}%)</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    return tableHTML;
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 添加CSS样式（动态添加）
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .notification-success {
        background: #28a745;
    }
    
    .notification-error {
        background: #dc3545;
    }
    
    .notification-info {
        background: #17a2b8;
    }
    
    .no-data {
        text-align: center;
        color: #666;
        font-size: 16px;
        padding: 40px;
    }
    
    .error {
        text-align: center;
        color: #dc3545;
        font-size: 16px;
        padding: 40px;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);