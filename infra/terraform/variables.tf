variable "aws_region" {
  description = "AWS region để deploy"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_id" {
  description = "VPC có sẵn để deploy vào (tạo trước hoặc dùng VPC mặc định)"
  type        = string
}

variable "subnet_ids" {
  description = "Danh sách subnet để chạy ECS task + RDS subnet group"
  type        = list(string)
}

variable "project_name" {
  description = "Prefix đặt tên cho mọi resource"
  type        = string
  default     = "mytasco-ai-workspace"
}

variable "environment" {
  description = "dev | staging | prod"
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Docker image của orchestrator (đẩy từ build-push.yml)"
  type        = string
  default     = "ghcr.io/your-org/mytasco-orchestrator:latest"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "db_username" {
  type    = string
  default = "mytasco_admin"
}

variable "db_password" {
  description = "Đặt qua terraform.tfvars hoặc biến môi trường TF_VAR_db_password, KHÔNG commit"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "Đặt qua TF_VAR_openai_api_key hoặc AWS Secrets Manager, KHÔNG commit"
  type        = string
  sensitive   = true
  default     = ""
}

