terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)
}

module "vpc" {
  source = "./modules/vpc"

  name_prefix        = var.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = local.azs
  tags               = var.tags
}

module "eks" {
  source = "./modules/eks"

  name_prefix       = var.name_prefix
  cluster_version   = var.eks_cluster_version
  subnet_ids        = module.vpc.private_subnet_ids
  node_instance_type = var.eks_node_instance_type
  desired_size      = var.eks_desired_size
  min_size          = var.eks_min_size
  max_size          = var.eks_max_size
  tags              = var.tags
}

module "rds" {
  source = "./modules/rds"

  name_prefix             = var.name_prefix
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  db_name                 = var.db_name
  db_username             = var.db_username
  db_password             = var.db_password
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  backup_retention_period = var.db_backup_retention_period
  tags                    = var.tags
}
