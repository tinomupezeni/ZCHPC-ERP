# CI/CD Pipeline Setup

This project uses GitHub Actions to automatically build and deploy the ZCHPC ERP system to a private VM using Docker images.

## Workflow Overview

1.  **Push to `main`:** Triggers the pipeline.
2.  **Build & Push:** GitHub Actions builds Docker images for the API, Main Frontend, and Employee Portal, then pushes them to Docker Hub.
3.  **Deploy:** Connects to the private VM via SSH, pulls the new images, and restarts the containers using `docker-compose`.

## GitHub Secrets Configuration

To enable the pipeline, you MUST configure the following secrets in your GitHub repository (**Settings > Secrets and variables > Actions**):

### Docker Hub Secrets
- `DOCKERHUB_USERNAME`: Your Docker Hub username (e.g., `tinotenda762`).
- `DOCKERHUB_TOKEN`: A Personal Access Token from Docker Hub.

### VM Access Secrets
- `SSH_HOST`: The IP address of your VM (e.g., `10.50.14.12`).
- `SSH_USER`: The username for SSH access (e.g., `ubuntu` or `root`).
- `SSH_PRIVATE_KEY`: Your SSH private key used to connect to the VM.
- `DEPLOY_PATH`: The directory on the VM where the `deploy/` folder is located (e.g., `/home/ubuntu/zchpc-erp/deploy`).

### Optional Frontend Config
- `VITE_API_URL_MAIN`: API URL for the main frontend (default: `https://zchpc-erp.zw`).
- `VITE_API_URL_PORTAL`: API URL for the employee portal (default: `https://portal.zchpc-erp.zw`).

---

## VM Setup Instructions

Before the pipeline can deploy successfully, the VM must be prepared:

### 1. Install Docker & Docker Compose
Ensure Docker and Docker Compose are installed on the VM.

### 2. Copy the `deploy/` Folder
Copy the `deploy/` folder from this repository to the `DEPLOY_PATH` on your VM.

### 3. Configure Environment Variables
Create a `.env` file inside the `deploy/` folder on your VM with the following variables:

```bash
# Database Configuration
POSTGRES_DB=erp_db
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=your_secure_password

# Django Configuration
SECRET_KEY=your_django_secret_key
ADMIN_EMAIL=admin@zchpc-erp.zw
ADMIN_PASSWORD=your_admin_password
```

### 4. Initial Startup
On the VM, run:
```bash
cd /path/to/deploy
docker-compose up -d
```

---

## Troubleshooting

- **Build Failures:** Check the GitHub Actions logs for build errors. Ensure the Dockerfiles are present and valid.
- **SSH Connection Failures:** Verify the `SSH_HOST`, `SSH_USER`, and `SSH_PRIVATE_KEY`. Ensure the VM allows SSH connections from GitHub's IP ranges or has appropriate firewall rules.
- **Deployment Failures:** Check the logs on the VM: `docker-compose logs -f`.
