variable "name_prefix" {
  description = "Prefix used in resource names."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where RDS runs."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for RDS subnet group."
  type        = list(string)
}

variable "db_name" {
  description = "Database name."
  type        = string
}

variable "db_username" {
  description = "Database admin username."
  type        = string
}

variable "db_password" {
  description = "Database admin password."
  type        = string
  sensitive   = true
}

variable "instance_class" {
  description = "RDS instance class."
  type        = string
}

variable "allocated_storage" {
  description = "Storage size in GB."
  type        = number
}

variable "backup_retention_period" {
  description = "Backup retention in days."
  type        = number
}

variable "tags" {
  description = "Tags applied to all RDS resources."
  type        = map(string)
  default     = {}
}
