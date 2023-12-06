pipeline de integração contínua

CI (Continuous Integration)
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
      - name: Docker build
        uses: docker/build-push-action@v3.2.0
        with:
          context: ./src
  CD:

  

