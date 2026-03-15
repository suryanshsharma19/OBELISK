output "cluster_name" {
  value       = aws_eks_cluster.this.name
  description = "EKS cluster name."
}

output "cluster_endpoint" {
  value       = aws_eks_cluster.this.endpoint
  description = "EKS API endpoint."
}

output "cluster_arn" {
  value       = aws_eks_cluster.this.arn
  description = "EKS cluster ARN."
}
