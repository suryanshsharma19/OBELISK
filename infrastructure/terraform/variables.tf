variable "aws_region" {
  description = "AWS region for OBELISK infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
  default     = "obelisk"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use."
  type        = number
  default     = 2
}

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS."
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_type" {
  description = "EC2 type for EKS managed nodes."
  type        = string
  default     = "t3.large"
}

variable "eks_desired_size" {
  description = "Desired EKS node count."
  type        = number
  default     = 2
}

variable "eks_min_size" {
  description = "Minimum EKS node count."
  type        = number
  default     = 1
}

variable "eks_max_size" {
  description = "Maximum EKS node count."
  type        = number
  default     = 4
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "obelisk"
}

variable "db_username" {
  description = "PostgreSQL admin username."
  type        = string
  default     = "obelisk"
}

variable "db_password" {
  description = "PostgreSQL admin password."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Initial RDS storage size in GB."
  type        = number
  default     = 30
}

variable "db_backup_retention_period" {
  description = "RDS backup retention in days."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default = {
    project     = "obelisk"
    environment = "production"
    managed_by  = "terraform"
  }
}
