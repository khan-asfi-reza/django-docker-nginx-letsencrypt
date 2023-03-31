# django-docker-nginx with  certbot

 - Follow the following steps to setup django api with nginx, certbot, elasticsearch, redis and postgresdb

#### Techs used

- Django
- Celery
- Postgresql
- Redis
- Elasticsearch
- Nginx
- Certbot


### Deploy this app in any vm instance 
- What you will need?
- amazon ec2, Google Compute Engine, DigitalOcean Instance, Azure VM

### Steps
* 
> SSH Into your VM

* 
>  Download and install Docker

( Example for Ubuntu/Debian Based Systems )

```shell
# App Environment 
sudo su

mkdir /home/app -p

cd /home/app

apt-get update
```

Remove old versions of docker and install latest ( Steps taken from official docker page, [View More](https://docs.docker.com/engine/install/ubuntu/))
```shell
# Uninstall Old Versions
apt-get remove docker docker-engine docker.io containerd runc
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

Add Docker Repo
```shell
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Update apt and install docker
```shell
# Install docker engine
apt-get update -y
# Install docker
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# Install docker-compose package
apt-get install -y docker-compose-plugin docker-compose
```

For other os [visit docker official documentation](https://docs.docker.com/engine/install/)


*
> Setup Github repo 