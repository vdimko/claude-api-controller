db = db.getSiblingDB('claude_api');

db.createUser({
  user: 'claude_user',
  pwd: 'claude_pass_2024',
  roles: [{ role: 'readWrite', db: 'claude_api' }]
});

db.createCollection('tasks');

db.tasks.createIndex({ "task_id": 1 }, { unique: true });
db.tasks.createIndex({ "agent_name": 1 });
db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "created_at": -1 });
db.tasks.createIndex({ "agent_name": 1, "created_at": -1 });
