
## build容器镜像

```bash
docker build -t ubuntu/testssh2:22.04 .
```

## 启动容器

执行docker_start.sh即可。如需要更改端口或数量，修改该文件即可。

```bash
sh docker_start.sh
```

docker_start.sh示例，第一个端口是映射到容器的22端口即`ssh`，后面两个为预留端口，第二个映射容器的8888端口，第三个映射容器的9999端口。

```sh
#!/bin/sh
sh run.sh 8301 8311 8321
sh run.sh 8302 8312 8322
sh run.sh 8303 8313 8323
sh run.sh 8304 8314 8324
```

