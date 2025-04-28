steps for build:

cd frontend_service
docker build -t frontend_service .
docker run -p 8080:8080 frontend_service
