FROM jenkins/jenkins:lts-jdk17

USER root

COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

RUN apt-get update && apt-get install -y curl unzip && \
    curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/aws.zip && \
    unzip -q /tmp/aws.zip -d /tmp && /tmp/aws/install && \
    curl -sSL "https://releases.hashicorp.com/terraform/1.10.5/terraform_1.10.5_linux_amd64.zip" -o /tmp/tf.zip && \
    unzip -q /tmp/tf.zip -d /usr/local/bin && \
    rm -rf /tmp/* /var/lib/apt/lists/*
