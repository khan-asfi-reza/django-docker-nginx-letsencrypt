# django-docker-nginx-letsencrypt

Purpose: Create a dockerized django application with nginx and ssl certificate.
This project covers how to deploy a django application with docker nginx letsencrypt (ssl certificate)
By following this repo, you will be able to publish your django app in any vm, and you will be able to
create a http-secured app

#### 💻 Techs used

- Django
- Celery
- Postgresql
- Redis
- Elasticsearch
- Nginx
- Certbot

#### 📂 Directory structure

```
---- docker ( Contains Docker Related Config Files )
     --- certbot
         --- Dockerfile
         --- certify.sh
     --- nginx
         --- Dockerfile
         --- nginx.conf ( Contains Both HTTPS and HTTP Config )
         --- nginx_http.conf ( Contains HTTP Config only )
         --- run.sh
     --- worker
         --- ...
         
---- blogs_api ( Django Application | Celery Application )
     --- ...
     --- apps
     --- blogs_api
         --- ...
         --- settings.py
```

### Explanations 📖

In `docker/nginx` directory there are two files 

* nginx.conf
* nginx_http.conf

`nginx_http.conf` will be used first to setup a http nginx server, which is important to get
the ssl certificate for the domain. Later after getting ssl certificate `nginx.conf` will be used which will
have https server


### 🎉 Deploy this app in any vm instances 
- What you will need?
- amazon ec2, Google Compute Engine, DigitalOcean Instance, Azure VM

### 🪜 Steps

### SSH Into your VM

SSH into your vm using ssh tool, you can use third party ssh tool like putty

### Download and install Docker 🐋

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


### Setup Github repo 😺

To get our codebase from github repo we need to generate a ssh deploy key
and put the deploy key public key to Github repo deploy key section

```shell
ssh-keygen -t ed25519 -C "GitHub Deploy Key"
```

Cat the public and copy and paste it in the github deploy keys section

Github Repo > Settings > Deploy Keys

```shell
cat ~/.ssh/id_ed25519.pub
```

The following command will cat the public key

```shell
ssh-ed25519 AAAAC3NzaD23ZDI1NTE5ABSFGKoH0ASXx2ua/++wZgCUSDGsg6VmPc/ys7vNSDGsd2D6 GitHub Deploy Key
```

Setting deploy key

![alt Image](https://github.com/khan-asfi-reza/django-docker-nginx-letsencrypt/blob/main/images/image1.png)

Put public key `ssh-ed25519 AAAAC3NzaD23ZDI1NTE5ABSFGKoH0ASXx2ua/++wZgCUSDGsg6VmPc/ys7vNSDGsd2D6 GitHub Deploy Key` In the `Key` section

![alt Image](https://github.com/khan-asfi-reza/django-docker-nginx-letsencrypt/blob/main/images/image2.png)


### Pull code from github repo

```shell
git init
```

Add your repo origin git url

```shell
git remote add origin <OriginURL>
```

Here for example I am pulling from main
```shell
git pull origin main
```
### Setup environment variable 💲

Create .env file where your environment variables will be stored
```shell
nano .env
```

```dotenv
DOMAIN=<DOMAIN>
ACME_DEFAULT_EMAIL=<EMAIL>
ENV=PROD
SECRET_KEY=<SECRET_KEY>
ENCRYPTION_KEY=<ENCRYPTION_KEY>
POSTGRES_DB=POSTGRES_DB
POSTGRES_USER=POSTGRES_USER
POSTGRES_PASSWORD=POSTGRES_PASSWORD
DATABASE_URL=postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@db:5432/<POSTGRES_DB>
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
AWS_STORAGE_BUCKET_NAME=<AWS_STORAGE_BUCKET_NAME>
AWS_S3_REGION_NAME=<AWS_S3_REGION_NAME>
AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY
AWS_SECRET_ACCESS_KEY_ID=AWS_SECRET_ACCESS_KEY_ID
AWS_S3_ENDPOINT_URL=AWS_S3_ENDPOINT_URL
AWS_LOCATION=static
DEBUG=False
EMAIL_HOST=EMAIL_HOST
EMAIL_HOST_USER=EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=EMAIL_HOST_PASSWORD
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=DEFAULT_FROM_EMAIL
ACCESS_TOKEN_LIFETIME=ACCESS_TOKEN_LIFETIME
REFRESH_TOKEN_LIFETIME=REFRESH_TOKEN_LIFETIME
ELASTICSEARCH_HOST=http://elasticsearch:9200
```

### Configure and run docker 🐋

Build docker containers
```shell
docker-compose -f docker-compose.prod.yaml build 
```

Run certbot command to get initial ssl certificate
```shell
docker-compose -f docker-compose.prod.yaml run -rm certbot /opt/certify.sh
```

Restart containers

```shell
docker-compose -f docker-compose.prod.yaml down
```

```shell
docker-compose -f docker-compose.prod.yaml up -d
```

### Crontab to renew ssl certificate 📜

The actions mentioned above will produce the first certificate for our project.
The certificate will only be valid for three months, 
therefore you must run the renew command earlier than that.

Create a bash script
```shell
nano rewnew.sh
```

This bash script will renew certificate
```shell
#!/bin/sh
set -e

cd /home/app/

/usr/local/bin/docker-compose -f docker-compose.prod.yaml run --rm certbot certbot renew
```

Give execution permission
```shell
chmod +x renew.sh
```

Open crontab
```shell
crontab -e
```

Add the following in the crontab
```
0 0 * * 6 sh /home/app/renew.sh
```

### Automated deploy using github actions 🎬

Create an SSH Key

```shell
ssh-keygen -t rsa -b 4096
```

Copy content of the key file

```shell
cat /.ssh/id_rsa
```

Add public key to the authorized key file

```shell
cat /.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

Create a bash script to deploy
```shell
nano deploy.sh
```

This bash script will renew certificate
```shell
#!/bin/sh
set -e

cd /home/app/

git stash

git pull origin main --force

/usr/local/bin/docker-compose -f docker-compose.prod.yaml up --build -d
```

Give execution permission
```shell
chmod +x deploy.sh
```


### Setup Github Actions

- Go to “Settings > Secrets > Actions”
- 
![alt Image](https://github.com/khan-asfi-reza/django-docker-nginx-letsencrypt/blob/main/images/image3.png)


Open the Actions tab and set secrets

![alt Image](https://github.com/khan-asfi-reza/django-docker-nginx-letsencrypt/blob/main/images/image4.png)


Create the following secrets:
SSH_PRIVATE_KEY: content of the private key file

SSH_USER: user to access the server (root)

SSH_HOST: hostname/ip-address of your server

WORK_DIR: path to the directory containing the repository ( For this /home/app)

MAIN_BRANCH: name of the main branch (mostly main)

![alt Image](https://github.com/khan-asfi-reza/django-docker-nginx-letsencrypt/blob/main/images/image5.png)


In your repo create

".github" > "workflows" > "deploy.yaml"

```yaml
on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  run_pull:
    name: run pull
    runs-on: ubuntu-latest

    steps:
    - name: install ssh keys
      # check this thread to understand why its needed:
      # https://stackoverflow.com/a/70447517
      run: |
        install -m 600 -D /dev/null ~/.ssh/id_rsa
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
        ssh-keyscan -H ${{ secrets.SSH_HOST }} > ~/.ssh/known_hosts
    - name: connect and pull
      run: ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} "cd ${{ secrets.WORK_DIR }} && git checkout ${{ secrets.MAIN_BRANCH }} && /home/app/deploy.sh"
    - name: cleanup
      run: rm -rf ~/.ssh
```

