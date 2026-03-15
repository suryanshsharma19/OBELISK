output "db_endpoint" {
  value       = aws_db_instance.this.endpoint
  description = "PostgreSQL endpoint."
}

output "db_port" {
  value       = aws_db_instance.this.port
  description = "PostgreSQL port."
}

output "security_group_id" {
  value       = aws_security_group.this.id
  description = "Database security group ID."
}
