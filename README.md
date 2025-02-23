To run: 

```
docker-compose up --build
```

Swagger Endpoint: 
```
http://localhost:8080/docs
```

Start proxy locally: 
```
gcloud auth login
cloud-sql-proxy nimble-chess-449208-f3:us-central1:finn-sql --port 5432
```