## Configuration

Configuration files come in sets where there is one config.yml file and another for monitors within that particular configuration. This is meant to be stacked so that the top level configuration is used to pull all the ec2 instance information for multiple teams as a local cache to then be parsed by the subsequent configurations.

The configurations can have any naming format but I've tended towards `<environment>-config.yml` and `<environment>-monitor.yml`.