resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnets"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-subnets"
  })
}

resource "aws_security_group" "this" {
  name        = "${var.name_prefix}-db-sg"
  description = "OBELISK PostgreSQL access"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-sg"
  })
}

resource "aws_db_instance" "this" {
  identifier                 = "${var.name_prefix}-postgres"
  engine                     = "postgres"
  engine_version             = "15.7"
  instance_class             = var.instance_class
  allocated_storage          = var.allocated_storage
  storage_type               = "gp3"
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = var.db_password
  db_subnet_group_name       = aws_db_subnet_group.this.name
  vpc_security_group_ids     = [aws_security_group.this.id]
  publicly_accessible        = false
  multi_az                   = false
  backup_retention_period    = var.backup_retention_period
  deletion_protection        = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${var.name_prefix}-postgres-final"
  auto_minor_version_upgrade = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-postgres"
  })
}
