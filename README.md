# biz-mcp-gateway

OCR/文档识别 MCP 服务，支持医疗票据、证件、车辆、宠物等识别能力。

## 功能

- 医疗票据查验（电子发票、医保版、异步查验）
- 证件识别（身份证、银行卡、营业执照、护照、行驶证、驾驶证、户口本）
- 医疗文档识别（费用清单、门诊住院发票、病历、化验单）
- 通用 OCR（文字识别、二维码、PDF转图片）
- 保单识别（车险、寿险）
- 车辆识别（车牌、VIN码、登记证书）
- 医疗知识库查询
- 宠物识别（品种、行为、鼻纹、关键点检测）

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `API_BASE` | 否 | `http://192.168.199.121:16880` | 上游 API 地址 |
| `TOKEN` | 否 | 空 | API 鉴权 Token |
| `TIMEOUT` | 否 | `30` | 请求超时（秒） |

## 本地运行

```bash
# stdio 模式（默认，适用于 MCP 客户端）
python run.py

# http 模式（适用于自有服务器部署）
python run.py http
```

## MCP 服务配置

本服务使用 Python + FastMCP 实现，默认使用 STDIO 传输。

### MCP Client 配置

```json
{
  "mcpServers": {
    "biz-mcp-gateway": {
      "command": "python",
      "args": ["run.py"],
      "env": {
        "API_BASE": "https://ai.inspirvision.cn/s",
        "TOKEN": "",
        "TIMEOUT": "30"
      }
    }
  }
}


## 通过 pip 安装运行

```bash
pip install -e .
biz-mcp-gateway        # stdio 模式
biz-mcp-gateway http   # http 模式
```

## 部署到魔搭 MCP 广场

1. 将代码推送到 GitHub 仓库
2. 在 [魔搭 MCP 广场](https://modelscope.cn/mcp-square) 选择「自定义创建」
3. 填写 GitHub 仓库地址，托管类型选「可托管部署」
4. 配置环境变量 `API_BASE` 和 `TOKEN`
5. 平台自动部署，生成 SSE 地址

## License

MIT
