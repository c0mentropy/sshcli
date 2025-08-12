FROM ubuntu:22.04

RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list

RUN apt-get update && \
    apt-get install -y \
    vim \
    openssh-server \
    curl \
    && apt-get clean


RUN echo PermitRootLogin yes >> /etc/ssh/sshd_config

RUN echo 'root:admin123' | chpasswd

COPY start.sh /start.sh

RUN chmod +x start.sh

WORKDIR /root

EXPOSE 22
EXPOSE 8888
EXPOSE 9999

CMD ["/start.sh"]

