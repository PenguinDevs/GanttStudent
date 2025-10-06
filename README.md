<div align="center">
  <h1>GanttStudent</h1>
  <p>
    <a href="https://discord.gg/xq25Exwf3X">
      <img src="https://img.shields.io/discord/1393987779343679649?color=5865F2&label=discord&logo=discord&logoColor=white" alt="Discord" />
    </a>
  </p>
  <p>Collaborative Gantt chart desktop app built using PyQt6 for a year 12 VCE Software Development Units 3/4 SAT.</p>
</div>

<div>&nbsp;</div>

## Stacks used
- Python 3.11.5
- PyQt6
- MongoDB

## Setting up
### Client
Inside /src/client/.env:
```env
SERVER_ADDRESS="https://localhost:8080" # address of backend server app with port
```
### Server
Inside /src/server/.env:
```env
MONGO_USER="username"
MONGO_PASS="password"
MONGO_ADDRESS="cluster123.123abc.mongodb.net"
```

## Using it yourself
1. First set up a MongoDB server either [locally](https://www.mongodb.com/products/self-managed/community-edition) or through [MongoDB Atlas](https://www.mongodb.com/).
2. Set up the necessary env files above.
3. Run both the server and client applications.
```python
python3 ./src/server/app.py
```
```python
python3 ./src/client/app.py
```
