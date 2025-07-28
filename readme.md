# Initstack Project

## Services Overview

This Project Uses Docker Compose To Manage Multiple Services. Below Is The List Of Services And Their Details:

### Core Services

- **Nginx Service**: Web Server/Reverse Proxy (Port: 8080)
- **Backend Service**: Main Application Backend
- **Flower Service**: Celery Monitoring (Port: 5555)
- **Celery Worker Service**: Background Task Processing
- **Celery Beat Service**: Scheduled Task Processing

### Database Services

- **Elasticsearch Service**: Distributed Search & Analytics Engine
- **MongoDB Service**: Document Database
- **Redis Service**: In-Memory Data Store (Port: 8001)
- **RabbitMQ Service**: Message Broker (Port: 15672)

### Monitoring & Observability

- **Prometheus Service**: Metrics Collection (Port: 9090)
- **Jaeger Query Service**: Distributed Tracing UI (Port: 16686)
- **Jaeger Collector Service**: Trace Collection
- **OTel Collector Service**: OpenTelemetry Data Collection

### Additional Services

- **Mailpit Service**: Email Testing (Port: 8025)
- **Mongo Express Service**: MongoDB Admin UI (Port: 8081)
- **Dicebear Service**: Avatar Generation
- **SonarQube Service**: Code Quality (Port: 9000)
