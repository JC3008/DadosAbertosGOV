# Resumo

Este projeto visa automatizar a extração de dados fundamentalistas de empresas listadas na B3. Para padronizar a integração de código será usado Git Actions para criação de Pipelines CI/CD.

## Docker passo a passo.
Após clonar o repositório, execute o comando abaixo para fazer o Build da imagem Python com as bibliotecas necessárias. Será criado no Docker Desktop uma imagem chamada python_fundamentus com a tag latest.

* docker build -t python_fundamentus:latest . 

Após a construção da imagem, você estará apto a executar o script armazenado em /workspaces/app/fundamentus_extract.py

* docker run python_fundamentus:latest python3.9 /workspaces/app/fundamentus_extract.py
pipeline de integração contínua

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
      

  

