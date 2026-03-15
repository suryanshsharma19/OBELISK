output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "ID of the OBELISK VPC."
}

output "public_subnet_ids" {
  value       = module.vpc.public_subnet_ids
  description = "Public subnet IDs."
}

output "private_subnet_ids" {
  value       = module.vpc.private_subnet_ids
  description = "Private subnet IDs."
}

output "eks_cluster_name" {
  value       = module.eks.cluster_name
  description = "EKS cluster name."
}

output "eks_cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "EKS API endpoint."
}

output "rds_endpoint" {
  value       = module.rds.db_endpoint
  description = "RDS endpoint for PostgreSQL."
}
