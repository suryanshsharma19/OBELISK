variable "name_prefix" {
  description = "Prefix used in resource names."
  type        = string
}

variable "cluster_version" {
  description = "EKS cluster Kubernetes version."
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs where EKS should run."
  type        = list(string)
}

variable "node_instance_type" {
  description = "Instance type for managed node group."
  type        = string
}

variable "desired_size" {
  description = "Desired node group size."
  type        = number
}

variable "min_size" {
  description = "Minimum node group size."
  type        = number
}

variable "max_size" {
  description = "Maximum node group size."
  type        = number
}

variable "tags" {
  description = "Tags applied to all EKS resources."
  type        = map(string)
  default     = {}
}
