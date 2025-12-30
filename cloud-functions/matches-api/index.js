// 云函数入口文件
const cloud = require('tcb-admin-node');

// 初始化云开发环境
cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

// 获取数据库引用
const db = cloud.database();
const matchesCollection = db.collection('cs2Matches');

// 云函数入口函数
exports.main = async (event, context) => {
  const { path, httpMethod, queryStringParameters, body } = event;
  
  // 解析请求体
  let requestBody = {};
  if (body) {
    try {
      requestBody = JSON.parse(body);
    } catch (error) {
      console.error('解析请求体失败:', error);
    }
  }
  
  try {
    // 获取所有比赛
    if (path === '/api/matches' && httpMethod === 'GET') {
      const result = await matchesCollection.get();
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        body: JSON.stringify(result.data)
      };
    }
    
    // 获取单个比赛
    else if (path.match(/^\/api\/matches\/([^/]+)$/) && httpMethod === 'GET') {
      const matchId = path.match(/^\/api\/matches\/([^/]+)$/)[1];
      const result = await matchesCollection.doc(matchId).get();
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify(result.data)
      };
    }
    
    // 添加新比赛
    else if (path === '/api/matches' && httpMethod === 'POST') {
      const matchData = requestBody;
      // 设置创建时间
      matchData.createdAt = new Date();
      const result = await matchesCollection.add({ data: matchData });
      
      // 返回添加后的完整数据
      const newMatch = await matchesCollection.doc(result.id).get();
      return {
        statusCode: 201,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify(newMatch.data)
      };
    }
    
    // 删除比赛
    else if (path.match(/^\/api\/matches\/([^/]+)$/) && httpMethod === 'DELETE') {
      const matchId = path.match(/^\/api\/matches\/([^/]+)$/)[1];
      await matchesCollection.doc(matchId).remove();
      return {
        statusCode: 204,
        headers: {
          'Access-Control-Allow-Origin': '*'
        },
        body: ''
      };
    }
    
    // 处理OPTIONS请求（CORS预检）
    else if (httpMethod === 'OPTIONS') {
      return {
        statusCode: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        body: ''
      };
    }
    
    // 未匹配的路由
    else {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ error: 'Not Found' })
      };
    }
  } catch (error) {
    console.error('处理请求失败:', error);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: 'Internal Server Error', message: error.message })
    };
  }
};