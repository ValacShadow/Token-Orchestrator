# Token-Orchestrator

git clone https://github.com/ValacShadow/Token-Orchestrator

cd Token-Orchestrator

docker-compose up --build 

run redis on docker

python3 main.py

It can handle all query in O(1) time complexity

Endpoints:
POST /keys: Generate new keys.
Status: 201
GET /keys: Retrieve an available key for client use.
Status: 200 / 404 
Response: { "keyId": "<keyID>" } / {}
GET /keys/:id: Provide information (e.g., assignment timestamps) about a specific key.
Status: 200 / 404 
Response: 
{ 
"isBlocked" : "<true> / <false>", 
"blockedAt" : "<blockedTime>", 
"createdAt" : "<createdTime>" 
} / {}
DELETE /keys/:id: Remove a specific key, identified by :id, from the system.
Status: 200 / 404
PUT /keys/:id: Unblock a key for further use.
Status: 200 / 404
PUT /keepalive/:id: Signal the server to keep the specified key, identified by :id, from being deleted.
Status: 200 / 404


