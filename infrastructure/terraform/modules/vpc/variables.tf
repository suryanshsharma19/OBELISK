variable "name_prefix" {
  description = "Prefix used in resource names."
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block."
  type        = string
}

variable "availability_zones" {
  description = "Availability zones used to spread subnets."
  type        = list(string)
}

variable "tags" {
  description = "Tags applied to all VPC resources."
  type        = map(string)
  default     = {}
}
