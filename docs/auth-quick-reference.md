# Authentication Quick Reference Guide

## 🚀 Quick Start

### 1. Login and Get JWT Token
```bash
POST /api/v1/iam/secure-auth/token
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "your_password"
}
```

### 2. Use Token in Requests
```bash
GET /api/v1/your-endpoint
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Protect Routes with Dependencies
```python
from src.iam.presentation.dependencies.jwt_dependencies import (
    JWTAuth, require_permission, require_role
)

@router.get("/protected")
def protected_endpoint(auth = JWTAuth):
    return {"user_id": auth.user_id}

@router.delete("/admin-only")
def admin_endpoint(auth = require_role("admin")):
    return {"success": True}
```

---

## 🔐 Authentication Dependencies

| Dependency | Description | Usage |
|------------|-------------|-------|
| `JWTAuth` | Basic JWT authentication | `auth = JWTAuth` |
| `CurrentUser` | Get current user info | `user = CurrentUser` |
| `JWTAuthWithOrg` | Requires organization context | `auth = JWTAuthWithOrg` |
| `require_permission("perm")` | Requires specific permission | `auth = require_permission("user:read")` |
| `require_role("role")` | Requires specific role | `auth = require_role("admin")` |
| `require_any_permission(*perms)` | Requires any of the permissions | `auth = require_any_permission("read", "write")` |
| `require_all_permissions(*perms)` | Requires all permissions | `auth = require_all_permissions("read", "write")` |

---

## 📋 Permission Format

| Pattern | Example | Description |
|---------|---------|-------------|
| `resource:action` | `user:read` | Specific permission |
| `resource:*` | `user:*` | All actions on resource |
| `*:action` | `*:read` | Action on all resources |
| `*:*` | `*:*` | Full access (super admin) |

---

## 🌐 API Endpoints

### Standard Auth (`/api/v1/iam/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User authentication |
| POST | `/logout` | Session logout |
| POST | `/refresh` | Token refresh |
| GET | `/validate` | Token validation |

### Secure Auth (`/api/v1/iam/secure-auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token` | Enhanced JWT generation (15min TTL) |
| POST | `/validate` | Secure token validation |
| POST | `/refresh` | Secure token refresh |

---

## ⚙️ Configuration

### Environment Variables
```bash
# Required
JWT_SECRET_KEY=your-secret-key-32-chars-minimum
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional (with defaults)
JWT_ALGORITHM=RS256                 # or HS256
JWT_EXPIRATION_MINUTES=15           # Short-lived tokens
JWT_REFRESH_EXPIRATION_HOURS=24     # Refresh window
SESSION_EXPIRATION_HOURS=24         # Session lifetime
SESSION_REMEMBER_ME_HOURS=720       # 30 days
```

---

## 💡 Common Usage Patterns

### Route Protection
```python
# Public route
@router.get("/public")
def public_endpoint():
    return {"public": True}

# Authenticated route
@router.get("/profile")
def get_profile(auth = JWTAuth):
    return {"user_id": auth.user_id}

# Permission-based route
@router.get("/users")
def list_users(auth = require_permission("user:read")):
    return {"users": get_users()}

# Role-based route
@router.delete("/admin")
def admin_action(auth = require_role("admin")):
    return {"admin": True}

# Organization-scoped route
@router.get("/org-data")
def get_org_data(auth = JWTAuthWithOrg):
    return {"org_id": auth.organization_id}
```

### Custom Authorization
```python
@router.post("/custom")
def custom_auth(auth = JWTAuth):
    # Custom permission logic
    if not auth.has_permission("custom:action"):
        raise HTTPException(403, "Permission denied")
    
    # Custom role logic
    if not auth.has_role("special_role"):
        raise HTTPException(403, "Role required")
    
    return {"authorized": True}
```

### Multi-Tenant Context
```python
@router.get("/tenant-data")
def get_tenant_data(auth = JWTAuthWithOrg):
    # Organization ID is guaranteed to be present
    data = get_data_for_organization(auth.organization_id)
    return {
        "organization_id": auth.organization_id,
        "data": data,
        "user_permissions": auth.permissions
    }
```

---

## 🔍 JWT Token Inspection

```python
# In your route handler
@router.get("/token-info")
def token_info(auth = JWTAuth):
    return {
        "user_id": auth.user_id,
        "organization_id": auth.organization_id,
        "email": auth.email,
        "permissions": auth.permissions,
        "roles": auth.roles,
        "user_agent": auth.user_agent,
        "ip_address": auth.ip_address,
        "expires_at": auth.token_payload.exp
    }
```

---

## 🚨 Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 401 | `Invalid email or password` | Login failed |
| 401 | `Authorization header required` | Missing token |
| 401 | `Invalid or expired token` | Token issues |
| 403 | `Permission required: user:read` | Missing permission |
| 403 | `Role required: admin` | Missing role |
| 403 | `Organization context required` | No org context |

---

## 🛠️ Development Tips

### Testing Auth in Development
```python
# Create test user with permissions
test_user = create_user("test@example.com", "password")
assign_permissions(test_user, ["user:read", "user:write"])
assign_role(test_user, "admin")

# Get token for testing
response = client.post("/api/v1/iam/secure-auth/token", json={
    "email": "test@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Use in tests
headers = {"Authorization": f"Bearer {token}"}
response = client.get("/protected-endpoint", headers=headers)
```

### Debug Token Contents
```python
from src.iam.domain.services.jwt_service import JWTService

jwt_service = JWTService()
payload = jwt_service.decode_token(token)
print(f"User ID: {payload.user_id}")
print(f"Permissions: {payload.permissions}")
print(f"Expires: {payload.exp}")
```

### Session Management
```python
# List user sessions
sessions = get_user_sessions(user_id)

# Revoke specific session
revoke_session(session_id)

# Revoke all user sessions (force logout everywhere)
revoke_all_user_sessions(user_id)
```

---

## 🔒 Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong JWT_SECRET_KEY (32+ characters)
- [ ] Use RS256 algorithm in production
- [ ] Implement token refresh logic
- [ ] Set up proper CORS
- [ ] Log security events
- [ ] Monitor session activity
- [ ] Implement rate limiting
- [ ] Use secure headers
- [ ] Validate all inputs

---

## 📞 Support

For questions about the authentication system:
1. Check the [full documentation](./authentication-system.md)
2. Review the code examples above
3. Look at existing route implementations
4. Check the test files for usage patterns

Remember: Always test authentication flows thoroughly and follow security best practices!