#!/bin/bash

# OBELISK Project Structure Setup Script
# For EndeavourOS (Arch-based)
# Description: AI-Powered Supply Chain Attack Detector

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project name
PROJECT_NAME="OBELISK"
PROJECT_DIR="./OBELISK"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║           OBELISK Project Structure Setup                ║"
echo "║     AI-Powered Supply Chain Attack Detector              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if directory already exists
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Directory $PROJECT_DIR already exists!${NC}"
    read -p "Do you want to continue? This will create subdirectories. (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Setup cancelled.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}📁 Creating project directory: $PROJECT_DIR${NC}"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

echo -e "${BLUE}🚀 Creating directory structure...${NC}"

# Create .github directory structure
echo -e "${YELLOW}📂 Creating .github workflows...${NC}"
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE

# Create backend directory structure
echo -e "${YELLOW}📂 Creating backend structure...${NC}"
mkdir -p backend/app/{api/routes,core,models,schemas,ml,services,db/migrations/versions,utils,workers}
mkdir -p backend/ml_models/{datasets/{malicious_code,benign_code,dependency_graphs},train,saved_models/codebert_finetuned,notebooks}
mkdir -p backend/tests/{test_api,test_ml,test_services,test_integration}
mkdir -p backend/scripts

# Create frontend directory structure
echo -e "${YELLOW}📂 Creating frontend structure...${NC}"
mkdir -p frontend/public
mkdir -p frontend/src/{components/{common,Dashboard,PackageAnalysis,PackageList,Alerts,Crawler,Settings},pages,hooks,services,utils,store/{slices,middleware},styles}

# Create infrastructure directory structure
echo -e "${YELLOW}📂 Creating infrastructure structure...${NC}"
mkdir -p infrastructure/docker/nginx
mkdir -p infrastructure/kubernetes
mkdir -p infrastructure/terraform/modules/{vpc,eks,rds}

# Create docs directory structure
echo -e "${YELLOW}📂 Creating docs structure...${NC}"
mkdir -p docs/{diagrams,api}

# Create scripts directory
echo -e "${YELLOW}📂 Creating scripts directory...${NC}"
mkdir -p scripts

# Create monitoring directory structure
echo -e "${YELLOW}📂 Creating monitoring structure...${NC}"
mkdir -p monitoring/{prometheus,grafana/{dashboards,provisioning},alerts}

echo -e "${GREEN}✅ All directories created successfully!${NC}"

# Create essential __init__.py files for Python packages
echo -e "${BLUE}🐍 Creating Python package files...${NC}"
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/routes/__init__.py
touch backend/app/core/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/ml/__init__.py
touch backend/app/services/__init__.py
touch backend/app/db/__init__.py
touch backend/app/utils/__init__.py
touch backend/app/workers/__init__.py
touch backend/ml_models/train/__init__.py
touch backend/tests/__init__.py
touch backend/tests/test_api/__init__.py
touch backend/tests/test_ml/__init__.py
touch backend/tests/test_services/__init__.py
touch backend/tests/test_integration/__init__.py

echo -e "${GREEN}✅ Python package files created!${NC}"

# Create essential placeholder files
echo -e "${BLUE}📝 Creating placeholder files...${NC}"

# Root files
cat > README.md << 'EOF'
# OBELISK - AI-Powered Supply Chain Attack Detector

🔒 Comprehensive security platform for detecting malicious packages in software supply chains.

## 🚀 Quick Start

```bash
# Start all services
docker-compose up

# Access the application
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

## 📖 Documentation

See `/docs` folder for detailed documentation.

## 🛠️ Development

See `docs/DEVELOPMENT.md` for development setup.

## 📝 License

MIT License - see LICENSE file for details.
EOF

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnp/
.pnp.js

# Testing
.coverage
htmlcov/
.pytest_cache/
coverage/

# Build
dist/
build/

# Docker
*.pid

# ML Models
*.pt
*.pth
*.pkl
*.h5
*.ckpt

# Jupyter
.ipynb_checkpoints/

# Terraform
*.tfstate
*.tfstate.backup
.terraform/

# Secrets
secrets/
*.pem
*.key
EOF

cat > .gitattributes << 'EOF'
# Auto detect text files and normalize line endings
* text=auto

# Source code
*.py text
*.js text
*.jsx text
*.ts text
*.tsx text
*.json text
*.yaml text
*.yml text
*.md text

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary
EOF

cat > .editorconfig << 'EOF'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,js,jsx,ts,tsx}]
indent_style = space
indent_size = 4

[*.{json,yaml,yml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
EOF

cat > VERSION << 'EOF'
1.0.0
EOF

cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024 OBELISK Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to OBELISK will be documented in this file.

## [Unreleased]

### Added
- Initial project structure
- Backend FastAPI setup
- Frontend React setup
- Docker configuration

## [1.0.0] - TBD

### Added
- AI-powered package analysis
- Typosquatting detection
- Code pattern analysis
- Real-time monitoring dashboard
EOF

# Backend files
cat > backend/.env.example << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://obelisk:obelisk@postgres:5432/obelisk
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=obelisk_password
REDIS_HOST=redis
REDIS_PORT=6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production

# Registry APIs
NPM_REGISTRY_URL=https://registry.npmjs.org
PYPI_REGISTRY_URL=https://pypi.org/pypi

# ML Models
CODEBERT_MODEL_PATH=./ml_models/saved_models/codebert_finetuned
GNN_MODEL_PATH=./ml_models/saved_models/gnn_model.pt
ISOLATION_FOREST_PATH=./ml_models/saved_models/isolation_forest.pkl

# Sandbox
SANDBOX_TIMEOUT=30
SANDBOX_MEMORY_LIMIT=512m

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF

cat > backend/requirements.txt << 'EOF'
# FastAPI and dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
neo4j==5.16.0
redis==5.0.1

# ML/AI
torch==2.1.2
transformers==4.36.2
scikit-learn==1.4.0
torch-geometric==2.4.0

# Code Analysis
tree-sitter==0.20.4
tree-sitter-python==0.20.4

# Utils
httpx==0.26.0
python-Levenshtein==0.23.0
python-dotenv==1.0.0

# Task Queue
celery==5.3.6
celery[redis]==5.3.6

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# Code Quality
black==24.1.1
flake8==7.0.0
mypy==1.8.0
EOF

cat > backend/requirements-dev.txt << 'EOF'
-r requirements.txt

# Development tools
ipython==8.20.0
jupyter==1.0.0
jupyterlab==4.0.10

# Code formatting
autopep8==2.0.4
isort==5.13.2

# Debugging
ipdb==0.13.13
EOF

cat > backend/.dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
*.db
*.sqlite
EOF

cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

cat > backend/pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=app --cov-report=html --cov-report=term
EOF

cat > backend/README.md << 'EOF'
# OBELISK Backend

FastAPI backend for OBELISK supply chain security platform.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## Testing

```bash
pytest
```
EOF

# Frontend files
cat > frontend/.env.example << 'EOF'
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
EOF

cat > frontend/.dockerignore << 'EOF'
node_modules
npm-debug.log
build
.git
.env.local
.DS_Store
EOF

cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Expose port
EXPOSE 3000

# Start app
CMD ["npm", "start"]
EOF

cat > frontend/package.json << 'EOF'
{
  "name": "obelisk-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.6.5",
    "recharts": "^2.10.3",
    "lucide-react": "^0.309.0",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.1.0",
    "d3": "^7.8.5"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.33"
  }
}
EOF

cat > frontend/.eslintrc.json << 'EOF'
{
  "extends": "react-app",
  "rules": {
    "no-unused-vars": "warn",
    "no-console": "off"
  }
}
EOF

cat > frontend/.prettierrc << 'EOF'
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
EOF

cat > frontend/README.md << 'EOF'
# OBELISK Frontend

React frontend for OBELISK supply chain security platform.

## Setup

```bash
npm install
```

## Run

```bash
npm start
```

Visit http://localhost:3000

## Build

```bash
npm run build
```
EOF

# Docker Compose
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: obelisk-postgres
    environment:
      POSTGRES_DB: obelisk
      POSTGRES_USER: obelisk
      POSTGRES_PASSWORD: obelisk
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U obelisk"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:5.15-community
    container_name: obelisk-neo4j
    environment:
      NEO4J_AUTH: neo4j/obelisk_password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "obelisk_password", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: obelisk-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: obelisk-backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://obelisk:obelisk@postgres:5432/obelisk
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: obelisk_password
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: obelisk-frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    stdin_open: true
    tty: true

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
EOF

# Makefile
cat > Makefile << 'EOF'
.PHONY: help setup dev down clean test lint format

help:
	@echo "OBELISK Development Commands"
	@echo "============================"
	@echo "make setup   - Initial setup"
	@echo "make dev     - Start development environment"
	@echo "make down    - Stop all services"
	@echo "make clean   - Clean all containers and volumes"
	@echo "make test    - Run tests"
	@echo "make lint    - Run linters"
	@echo "make format  - Format code"

setup:
	@echo "Setting up OBELISK..."
	cd backend && python -m venv venv
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Setup complete!"

dev:
	docker-compose up

down:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

test:
	cd backend && pytest

lint:
	cd backend && flake8 app/
	cd frontend && npm run lint

format:
	cd backend && black app/
	cd frontend && npm run format
EOF

echo -e "${GREEN}✅ Placeholder files created!${NC}"

# Create project info file
cat > PROJECT_INFO.txt << EOF
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                   OBELISK PROJECT                        ║
║     AI-Powered Supply Chain Attack Detector              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Created: $(date)
Structure: Professional Production-Grade

📊 Project Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Directories: $(find . -type d | wc -l)
Total Files Created: $(find . -type f | wc -l)
Backend Python Packages: $(find backend -name "__init__.py" | wc -l)

📁 Main Directories:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ .github/          - CI/CD workflows
✓ backend/          - FastAPI Python backend
✓ frontend/         - React frontend
✓ infrastructure/   - Docker, Kubernetes, Terraform
✓ docs/            - Documentation
✓ scripts/         - Utility scripts
✓ monitoring/      - Prometheus, Grafana

🚀 Quick Start:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review README.md
2. Copy .env.example files and configure
3. Run: docker-compose up
4. Access:
   - Frontend: http://localhost:3000
   - Backend:  http://localhost:8000
   - API Docs: http://localhost:8000/docs

📝 Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Initialize git: git init
2. Start coding backend files (see implementation guides)
3. Use GitHub Copilot with provided prompts
4. Test frequently
5. Build incrementally

🎯 Development Order:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 1-2:  Backend core (config, models, database)
Week 3-4:  ML detectors (typosquat, code analyzer)
Week 5-6:  Services & API routes
Week 7-8:  Frontend components
Week 9-10: Integration & testing
Week 11-12: Documentation & polish

Good luck building OBELISK! 🚀
EOF

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    SETUP SUMMARY                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Statistics:${NC}"
echo "   Total directories created: $(find . -type d | wc -l)"
echo "   Total files created: $(find . -type f | wc -l)"
echo "   Python packages: $(find backend -name "__init__.py" | wc -l)"
echo ""
echo -e "${GREEN}📁 Project Structure:${NC}"
echo "   ✓ Backend (FastAPI)"
echo "   ✓ Frontend (React)"
echo "   ✓ Infrastructure (Docker, K8s)"
echo "   ✓ Documentation"
echo "   ✓ Monitoring"
echo ""
echo -e "${YELLOW}📝 Configuration Files Created:${NC}"
echo "   ✓ docker-compose.yml"
echo "   ✓ Makefile"
echo "   ✓ .gitignore"
echo "   ✓ .env.example files"
echo "   ✓ requirements.txt"
echo "   ✓ package.json"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "   1. cd OBELISK"
echo "   2. Review PROJECT_INFO.txt"
echo "   3. Review README.md"
echo "   4. Initialize git: git init"
echo "   5. Start coding: Use implementation guides"
echo ""
echo -e "${GREEN}✨ OBELISK project structure ready!${NC}"
echo ""
echo -e "${YELLOW}📖 See PROJECT_INFO.txt for detailed information${NC}"
echo ""
