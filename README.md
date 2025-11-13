# AWS Infrastructure MCP Server

Servidor Model Context Protocol (MCP) em Python que expõe ferramentas para inspecionar
recursos de infraestrutura AWS como EC2, S3 e RDS. O projeto utiliza `fastmcp` para
declarar as ferramentas MCP e `boto3` para consultar a AWS.

## Instalação

```bash
pip install .
```

Opcionalmente, instale as dependências de desenvolvimento:

```bash
pip install .[dev]
```

## Uso

Execute o servidor MCP via linha de comando. Ele utiliza I/O padrão, o que permite a
conexão direta com clientes MCP compatíveis:

```bash
aws-infra-mcp
```

### Ferramentas expostas

| Nome | Descrição |
| --- | --- |
| `listar_ec2` | Lista instâncias EC2, opcionalmente filtrando por estado. |
| `listar_buckets_s3` | Lista todos os buckets S3 disponíveis. |
| `listar_rds` | Lista instâncias RDS. |
| `resumo_conta` | Retorna um resumo com contagem das principais categorias acima. |

Cada ferramenta aceita os parâmetros opcionais `region` e `profile` para controlar a
sessão AWS utilizada. As credenciais devem estar configuradas previamente via variáveis
de ambiente, perfil do AWS CLI ou outro método suportado pelo `boto3`.
