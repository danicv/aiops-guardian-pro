variable "prefix" {
  type    = string
  default = "aiopsguardian"
}
variable "location" {
  type    = string
  default = "eastus2"
}
variable "environment" {
  type    = string
  default = "dev"
}
variable "node_count" {
  type    = number
  default = 2
}
variable "node_vm_size" {
  type    = string
  default = "Standard_D4s_v5"
}
variable "tags" {
  type = map(string)
  default = {
    product = "aiops-guardian-pro"
    owner   = "platform-engineering"
  }
}
