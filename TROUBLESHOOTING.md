# Troubleshooting - FastAPI DDD Project

## 307 Temporary Redirect em `/api/v1/users`

### Problema
Você pode ver logs como:
```
INFO: 127.0.0.1:44510 - "POST /api/v1/users HTTP/1.1" 307 Temporary Redirect
```

### Causa
FastAPI está redirecionando automaticamente devido a trailing slash. Isso acontece quando:

1. **Cliente envia**: `POST /api/v1/users/` (com slash final)
2. **FastAPI redireciona para**: `POST /api/v1/users` (sem slash final)

### Solução

#### Opção 1: Corrigir o Cliente
```bash
# ❌ Errado (com trailing slash)
curl -X POST http://localhost:5000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test"}'

# ✅ Correto (sem trailing slash)
curl -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test"}'
```

#### Opção 2: Desabilitar Redirecionamentos (Já implementado)
```python
app = FastAPI(redirect_slashes=False)
```

#### Opção 3: Suporte a Ambas as URLs (Já implementado)
```python
@router.post("/")     # /api/v1/users/
@router.post("")      # /api/v1/users
 def create_user(...):
```

### Endpoints Corretos
```
POST /api/v1/users          ✅ Funciona
GET  /api/v1/users          ✅ Funciona  
GET  /api/v1/users/{id}     ✅ Funciona
PUT  /api/v1/users/{id}     ✅ Funciona
DELETE /api/v1/users/{id}   ✅ Funciona
```

---

## Requisições para `/v1/models`

### Problema
Você pode ver logs como:
```
INFO: 127.0.0.1:36860 - "GET /v1/models HTTP/1.1" 404 Not Found
```

### Causa
Algumas ferramentas estão tentando usar sua aplicação FastAPI como se fosse uma API de modelos de IA (OpenAI-like). Isso pode acontecer por:

1. **Ferramentas de IA configuradas incorretamente**
   - Claude Code
   - Continue.dev
   - Cursor
   - Copilot
   - Outras extensões de IA

2. **Variáveis de ambiente apontando para localhost**
   ```bash
   OPENAI_API_BASE=http://localhost:8000
   OLLAMA_HOST=http://localhost:8000
   ```

3. **Proxies ou redirecionamentos**
   - Nginx ou outros proxies redirecionando tráfego
   - Docker networks mal configurados

### Solução

#### 1. Verificar Variáveis de Ambiente
```bash
# Verificar se há configurações apontando para sua app
env | grep -i api
env | grep -i localhost
env | grep -i 8000
```

#### 2. Verificar Ferramentas de IA
- **VS Code**: Verificar extensões como Continue, Cursor, Copilot
- **Claude Code**: Verificar configurações de base URL
- **Terminal**: Verificar aliases ou scripts

#### 3. Verificar Processos na Porta 8000
```bash
# Ver quem está usando a porta 8000
lsof -i :8000
netstat -tulpn | grep 8000
```

#### 4. Usar Porta Diferente
```bash
# Rodar sua app em porta diferente
poetry run uvicorn main:app --port 8080
# ou
poetry run dev --port 8080
```

### Monitoramento
A aplicação agora inclui:
- ✅ Endpoint `/v1/models` com resposta clara
- ✅ Logging de requisições suspeitas
- ✅ Handlers para endpoints comuns de IA

### Logs Úteis
Com as mudanças implementadas, você verá:
```
WARNING: AI API request detected: GET /v1/models from 127.0.0.1 User-Agent: python-requests/2.31.0
```

Isso ajuda a identificar qual ferramenta está fazendo as requisições.

### Verificação Rápida
```bash
# Testar se o endpoint agora responde adequadamente
curl http://localhost:8000/v1/models

# Deve retornar uma mensagem clara explicando que não é uma API de IA
```