# MCP 管理平台部署指南

## 架构概览

```
┌──────────────────────────────────────────────────────────┐
│                      宿主机                               │
│                                                          │
│  /home/pxy/configs/      ← JSON 配置文件（共享）           │
│  /home/pxy/nginx.conf    ← nginx 配置（admin自动生成）     │
│                                                          │
│  宿主机 nginx (:80)                                       │
│    location /mcp_server/ → proxy_pass :8000/mcp           │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │  mcp-admin   │   │ biz-mcp-     │   │ mcp-nginx-1  │  │
│  │  (Docker)    │   │ gateway × N  │   │ :8000→80     │  │
│  │  管理平台API  │   │ MCP 服务     │   │ 路由转发      │  │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘  │
│         │                  │                   │          │
│         └──────────────────┼───────────────────┘          │
│                            │                              │
│                     Docker Network                        │
│                     (mcp_default)                          │
└──────────────────────────────────────────────────────────┘
```

## 前置条件

- 服务器已安装 Docker
- 本地已安装 Docker Desktop
- 服务器宿主机已配置 nginx（转发 /mcp_server/ 到 8000 端口）

## 一、本地构建镜像

在项目根目录 `E:\code\mcp` 执行：

```bash
# 构建 MCP 服务镜像
docker build -t biz-mcp-gateway -f src/Dockerfile .

# 构建管理平台镜像
docker build -t mcp-admin -f admin/Dockerfile .
```

## 二、导出并上传到服务器

### 导出镜像

```bash
docker save biz-mcp-gateway > biz-mcp-gateway.tar
docker save mcp-admin > mcp-admin.tar
```

### 上传文件到服务器

```bash
# 上传镜像文件
scp biz-mcp-gateway.tar mcp-admin.tar root@你的服务器IP:/home/pxy/

# 上传配置文件
scp -r E:\code\mcp\configs root@你的服务器IP:/home/pxy/configs
```

## 三、服务器上加载并启动

SSH 登录服务器执行：

```bash
# 加载镜像
docker load < /home/pxy/biz-mcp-gateway.tar
docker load < /home/pxy/mcp-admin.tar

# 创建 Docker 网络
docker network create mcp_default

# 创建空 nginx.conf
touch /home/pxy/nginx.conf
```

### 启动顺序：先 admin，后 nginx

```bash
# 1. 启动 admin（自动生成 nginx.conf 和 docker-compose.yml）
docker run -d \
  --name mcp-admin \
  --network mcp_default \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker \
  -v /home/pxy/configs:/app/configs \
  -v /home/pxy/nginx.conf:/app/nginx.conf \
  mcp-admin

# 2. 启动 nginx（读取 admin 生成的 nginx.conf）
docker run -d \
  --name mcp-nginx-1 \
  --network mcp_default \
  --restart unless-stopped \
  -p 8000:80 \
  -v /home/pxy/nginx.conf:/etc/nginx/nginx.conf \
  nginx
```

### 验证

```bash
# 查看 admin 日志
docker logs -f mcp-admin

# 检查健康状态
docker exec mcp-admin curl -s http://localhost:9001/api/health
```

## 四、访问管理平台

### 宿主机 nginx 配置

在宿主机的 nginx 中添加：

```nginx
location /mcp_server/ {
    proxy_pass http://127.0.0.1:8000/mcp/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 访问地址

- 管理平台 API：`http://域名/mcp_server/api/health`
- MCP 服务：`http://域名/mcp_server/{服务路由路径}`

## 五、使用说明

### 启动服务

在「服务列表」页面点击「启动」按钮：

1. 自动创建并启动 MCP 容器
2. 自动配置 nginx 路由
3. 服务立即可用

### 停止服务

点击「停止」按钮：

1. 自动停止容器
2. 自动从 nginx 移除路由

### 批量操作

勾选多个服务后，可批量启动/停止/重启/删除。

### MCP 端点路由规则

| 服务名 | 访问路径 |
|--------|----------|
| pet_breed | /mcp_server/pet/breed |
| bird_detect | /mcp_server/bird/detect |
| medical_listing | /mcp_server/medical/listing |
| invoice_financial | /mcp_server/invoice/financial |
| insurance | /mcp_server/insurance |
| general | /mcp_server/general |

## 六、更新配置

配置文件在 `/home/pxy/configs/` 目录下，直接编辑 JSON 文件即可。

修改后重启 admin 容器：

```bash
docker restart mcp-admin
```

## 七、故障排查

```bash
# 查看 admin 日志
docker logs mcp-admin

# 查看某个 MCP 服务日志
docker logs mcp-{服务名}-1

# 查看 nginx 日志
docker logs mcp-nginx-1

# 查看所有容器状态
docker ps -a --filter "network=mcp_default"
```

### 常见问题

**RuntimeError: can't start new thread**

admin 所有路由使用 `async def` 避免线程池问题。如果仍然出现此错误，重建 admin 镜像：

```bash
docker build -t mcp-admin -f admin/Dockerfile .
docker save mcp-admin > mcp-admin.tar
scp mcp-admin.tar root@服务器IP:/home/pxy/

# 服务器上
docker load < /home/pxy/mcp-admin.tar
docker rm -f mcp-admin
# 用 DEPLOY.md 中的启动命令重新启动
```

## 八、清理

```bash
# 停止并删除所有容器
docker stop $(docker ps -a --filter "network=mcp_default" -q)
docker rm $(docker ps -a --filter "network=mcp_default" -q)

# 删除镜像
docker rmi biz-mcp-gateway mcp-admin

# 删除网络
docker network rm mcp_default
```
