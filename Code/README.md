## AIS ANALYTICS

Python, Vue Application supporting complex SpatioTemporal Queries

### Installation

Copy .env.template to .env in your root directory and fill in accord your settings


### Docker
```
docker-compose up
```

### Local Python - Dev

Tested On  Python3.7

```
python -m venv .venv 
```

#### Linux
```
source ./.vemv/bin/activate
```

```
uvicorn web:app  --host 0.0.0.0 --port 8000
```

Front End is build on Vue.js with Node 12, so install it.....use nvm

If you need to change API URI got to .env inside ui (or create it) and set

```
VUE_APP_API_URL=http://127.0.0.1:8000
```

Go to ./ui

```
nvm use 12
```

```
nvm install
```

```
nvm run serve
```