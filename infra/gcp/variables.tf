variable "project_id" {
  type = string
}
variable "region" {
  type    = string
  default = "us-east1"
}
variable "cluster_name" {
  type    = string
  default = "aiops-guardian"
}
variable "deploy_workloads" {
  type    = bool
  default = false
}
variable "mcp_image" {
  type    = string
  default = ""
}
variable "backend_image" {
  type    = string
  default = ""
}
variable "frontend_image" {
  type    = string
  default = ""
}
