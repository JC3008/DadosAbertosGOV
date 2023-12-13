# Resumo

Este projeto visa automatizar a extração de dados fundamentalistas de empresas listadas na B3. Para padronizar a integração de código será usado Git Actions para criação de Pipelines CI/CD.

## Clonagem do repositório.
Crie uma pasta localmente, e execute o comando git clone https://github.com/JC3008/Fundamentus_to_S3.git.

## Credenciais necessárias
Para executar o script de upload será necessário registrar aws_access_key_id e aws_secret_access_key no arquivo src\.env (Atenção para o fato de que esse é o caminho em que será registrado localmente o arquivo .env). Também atente para a região registrada. Caso utilize outra, altere no .env
Caso não tenha as credenciais, dentro do console da AWS, crie na sessão IAM > Users > Security Credentials.

* aws_access_key_id=xxxxxxxxxxxxxxxxxxxx
* aws_secret_access_key=xxxxxxxxxxxxxxxxxxxxxxxx
* aws_region=us-east-2=xxxxxxxxxxxx

## Docker passo a passo.
Após clonar o repositório, execute o comando abaixo para fazer o Build da imagem Python com as bibliotecas necessárias. Será criada no Docker Desktop uma imagem chamada python_fundamentus com a tag latest. 


* docker build -t python_fundamentus:latest . 

Após a construção da imagem, você será possível executar o script armazenado em /workspaces/app/fundamentus_extract.py

* docker run python_fundamentus:latest python3.9 /workspaces/app/fundamentus_extract.py
pipeline de integração contínua

## Entendendo o script.
O script de extração, carga e transformação de dados foi desenvolvido em Python, sendo que grande parte do script é orientado a objeto. Arquivos envolvidos:

* src\fundamentus_extract.py
* src\objects.py

Dentro do arquivo objects.py existem as classes construídas para padronizar as conexões, estrutura de pastas, logs e campos de metadados. Algumas classes importantes:

* folderpath: Esta classe visa construir estrutura de pastas yyyy/mm/dd
* aws_connection: Classe que busca as credenciais no arquivo .env e estabelece a conexão
* data_transfer: Classe que visa mover arquivos entre S3 buckets, adicionando alguns campos de metadados.

## CI (Continuous Integration)
integração de código visando agregar novas features de forma padronizada e automática.
etapas envolvidas (codificação, commit, build, teste, geração de pacote)

pipeline de entrega contínua
CD (Continuous Deployment)
etapas envolvidas (release, teste, aceite, deploy)

Github Actions
Workflow
Events
Jobs
Steps
Actions
Runners

Requisitos:
Cluster Kubernetes
Dockerfile

No Github:

Selecione Actions, e depois escolha a opção set up workflow yourself.

name: CI-CD

on: 
  push:
    branches: ["main"]

jobs:
  CI:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3.1.0

      - name: autentication docker hub
        uses: docker/login-action@v2.1.0
        with:
          username: ${{secrets.DOCKERHUB_USER}}
          password: ${{secrets.DOCKERHUB_PWD}}

      - name: Docker build
        uses: docker/build-push-action@v3.2.0
        with:
          context: ./src
          file: ./src/Dockerfile
          push: true
          tags:
            JC/DadosAbertosGOV:${{github.run_number}}
            JC/DadosAbertosGOV:latest
  
  CD:
    runs-on: ubuntu-latest
    needs: [CI]

    steps:
      - uses: actions/checkout@v3.1.0
      - name: Cluster Context
        uses: Azure/k8s-set-context@3.0
        with:
          method: kubeconfig
          kubeconfig: ${{secrets.k8s_CONFIG}}
      - name: Deploy to Kubernetes cluster
        uses: Azure/k8s-deploy@v4
        with:
          images: jcs7/fundamentus:v1.0
          manifests: k8s/deployment.yaml
      

  

