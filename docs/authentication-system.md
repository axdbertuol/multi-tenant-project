# JWT + Session Authentication System Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Authentication Endpoints](#authentication-endpoints)
3. [JWT Token Structure](#jwt-token-structure)
4. [Session Management](#session-management)
5. [Permission-Based Dependencies](#permission-based-dependencies)
6. [Configuration](#configuration)
7. [Security Features](#security-features)
8. [API Reference](#api-reference)
9. [Integration Examples](#integration-examples)
10. [Security Best Practices](#security-best-practices)

---

## Architecture Overview

The authentication system uses a **hybrid JWT + Session approach** that combines the performance benefits of JWT tokens with the management capabilities of database sessions.

### Key Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   JWT Tokens    │◄──►│  Database        │◄──►│  RBAC Service   │
│  (Stateless)    │    │  Sessions        │    │  (Permissions)  │
│                 │    │  (Stateful)      │    │                 │
│ • User ID       │    │ • JWT String     │    │ • User Roles    │
│ • Organization  │    │ • Device Info    │    │ • Permissions   │
│ • Permissions   │    │ • Revocation     │    │ • Inheritance   │
│ • Roles         │    │ • Audit Trail    │    │ • Scoping       │
│ • 15min TTL     │    │ • 24h/30d TTL    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Benefits

- **🚀 Performance**: Permissions embedded in JWT reduce database queries
- **🔒 Security**: Database sessions enable immediate token revocation
- **📊 Management**: Session tracking, device management, audit trails
- **🏢 Multi-tenant**: Organization context in every request
- **⚡ Scalability**: Stateless JWT tokens work across multiple servers

---

## Authentication Endpoints

### Base Authentication Routes (`/api/v1/iam/auth`)

#### `POST /auth/login`
Standard user authentication with JWT generation.

**Request:**
```json
{
  "email": "user@company.com",
  "password": "secure_password",
  "remember_me": false
}
```

**Response:**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "user@company.com",
    "is_active": true
  },
  "session": {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "expires_at": "2025-07-03T22:30:00Z",
    "is_valid": true,
    "is_expired": false
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### `POST /auth/logout`
Revoke user session(s).

**Request Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "revoke_all_sessions": false
}
```

#### `POST /auth/refresh`
Refresh JWT token with updated permissions.

**Request Headers:**
```
Authorization: Bearer <jwt_token>
```

#### `GET /auth/validate`
Validate JWT token and return user information.

**Request Headers:**
```
Authorization: Bearer <jwt_token>
```

### Secure Authentication Routes (`/api/v1/iam/secure-auth`)

#### `POST /secure-auth/token`
Enhanced JWT generation with full RBAC integration.

**Features:**
- Short-lived tokens (15 minutes)
- Embedded permissions and roles
- Client metadata tracking
- Enhanced security measures

**Request:**
```json
{
  "email": "admin@company.com",
  "password": "secure_password",
  "remember_me": false
}
```

**Response:**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Admin User",
    "email": "admin@company.com",
    "is_active": true
  },
  "session": {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "expires_at": "2025-07-03T22:30:00Z",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100",
    "is_valid": true
  },
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## JWT Token Structure

### Token Claims

```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "exp": 1672531200,
  "iat": 1672530300,
  "org_id": "456e7890-e89b-12d3-a456-426614174001",
  "email": "user@company.com",
  "permissions": [
    "user:read",
    "user:write", 
    "organization:read",
    "admin:*"
  ],
  "roles": [
    "admin",
    "user"
  ],
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.100"
}
```

### Claim Descriptions

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string | User ID (standard JWT subject) |
| `exp` | number | Expiration timestamp (standard JWT) |
| `iat` | number | Issued at timestamp (standard JWT) |
| `org_id` | string | Organization ID for multi-tenant context |
| `email` | string | User email address |
| `permissions` | array | User's effective permissions from RBAC |
| `roles` | array | User's role names |
| `user_agent` | string | Client user agent for security tracking |
| `ip_address` | string | Client IP address for security tracking |

### Permission Format

Permissions follow the format: `resource:action`

Examples:
- `user:read` - Read user information
- `user:write` - Create/update users
- `organization:admin` - Full organization administration
- `admin:*` - All admin permissions (wildcard)
- `*:read` - Read access to all resources (wildcard)
- `*:*` - Full access (super admin)

---

## Session Management

### Session Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ACTIVE    │───►│  EXPIRED    │    │ LOGGED_OUT  │    │   REVOKED   │
│             │    │             │    │             │    │             │
│ Normal use  │    │ Time limit  │    │ User logout │    │ Admin/       │
│ JWT valid   │    │ reached     │    │ JWT invalid │    │ Security     │
│             │    │ JWT invalid │    │             │    │ JWT invalid  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                               ▲                    ▲
       └───────────────────────────────┘                    │
                                                             │
                          ┌─────────────────────────────────┘
                          │
                    Force revocation
```

### Session Properties

```python
class UserSession:
    id: UUID
    user_id: UUID
    session_token: str  # JWT token string
    expires_at: datetime
    created_at: datetime
    last_activity_at: datetime
    user_agent: Optional[str]
    ip_address: Optional[str]
    status: SessionStatus  # ACTIVE, EXPIRED, LOGGED_OUT, REVOKED
```

### Session Operations

#### Create Session
```python
session = create_session(
    user=user,
    token=jwt_token,  # Store JWT string
    duration_hours=24,
    user_agent="Mozilla/5.0...",
    ip_address="192.168.1.100"
)
```

#### Revoke Session
```python
# Single session
revoke_session(jwt_token)

# All user sessions
revoke_all_user_sessions(user_id)
```

#### Session Validation
```python
def validate_token(jwt_token):
    # 1. Try JWT validation (fast)
    if jwt_service.is_token_valid(jwt_token):
        return get_user_from_jwt(jwt_token)
    
    # 2. Check session in database
    session = get_session_by_token(jwt_token)
    if session and session.is_valid():
        return get_user_from_session(session)
    
    return None
```

---

## Permission-Based Dependencies

### FastAPI Dependencies

#### Basic Authentication
```python
from src.iam.presentation.dependencies.jwt_dependencies import (
    JWTAuth, CurrentUser, JWTAuthWithOrg
)

@router.get("/profile")
def get_profile(current_user = CurrentUser):
    return {"user": current_user}

@router.get("/dashboard")
def get_dashboard(auth_context = JWTAuth):
    return {
        "user_id": auth_context.user_id,
        "permissions": auth_context.permissions,
        "organization": auth_context.organization_id
    }
```

#### Permission-Based Authorization
```python
from src.iam.presentation.dependencies.jwt_dependencies import (
    require_permission, require_role, require_any_permission
)

@router.get("/users")
def list_users(auth = require_permission("user:read")):
    return {"users": get_users()}

@router.delete("/users/{user_id}")
def delete_user(user_id: str, auth = require_role("admin")):
    return {"deleted": user_id}

@router.post("/organizations")
def create_org(auth = require_any_permission("org:create", "admin:*")):
    return {"created": True}
```

#### Organization Context
```python
@router.get("/org-data")
def get_org_data(auth = JWTAuthWithOrg):
    # Ensures organization_id is present in JWT
    return {"organization_id": auth.organization_id}
```

### Permission Checking Methods

#### In JWT Authentication Context
```python
auth_context = get_jwt_auth_context(request)

# Check specific permission
if auth_context.has_permission("user:write"):
    # User can create/update users
    pass

# Check role
if auth_context.has_role("admin"):
    # User has admin role
    pass

# Access user information
user_id = auth_context.user_id
organization_id = auth_context.organization_id
permissions = auth_context.permissions
```

#### In JWT Service
```python
jwt_service = JWTService()

# Check permission from token
if jwt_service.has_permission(jwt_token, "user:read"):
    # Permission granted
    pass

# Get permissions from token
permissions = jwt_service.get_token_permissions(jwt_token)
roles = jwt_service.get_token_roles(jwt_token)
```

---

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-must-be-at-least-32-characters-long
JWT_ALGORITHM=RS256
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_HOURS=24

# Session Configuration
SESSION_EXPIRATION_HOURS=24
SESSION_REMEMBER_ME_HOURS=720

# Database Configuration
DATABASE_URL=postgresql://admin:admin123@localhost:5432/ddd_app
```

### Settings Configuration

```python
class Settings(BaseSettings):
    # JWT settings
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=15, env="JWT_EXPIRATION_MINUTES")
    
    # Session settings
    session_expiration_hours: int = Field(default=24, env="SESSION_EXPIRATION_HOURS")
    session_remember_me_hours: int = Field(default=720, env="SESSION_REMEMBER_ME_HOURS")
    
    @property
    def jwt_expiration_delta(self) -> timedelta:
        return timedelta(minutes=self.jwt_expiration_minutes)
```

---

## Security Features

### Token Security
- **Short-lived JWTs**: 15-minute default expiration
- **Algorithm flexibility**: Supports RS256 (recommended) and HS256
- **Secure generation**: Uses `python-jose[cryptography]`
- **Payload validation**: Comprehensive token structure validation

### Session Security
- **Immediate revocation**: Database sessions enable instant logout
- **Device tracking**: User agent and IP address logging
- **Concurrent session limits**: Can implement session count limits
- **Activity monitoring**: Last activity timestamp tracking

### Client Security
- **Metadata tracking**: IP address and user agent in both JWT and session
- **Anomaly detection**: Can detect logins from new devices/locations
- **Audit trail**: Complete login/logout history
- **Security headers**: Proper WWW-Authenticate headers in responses

### Error Security
- **Information hiding**: Generic error messages to prevent enumeration
- **Secure logging**: Detailed errors logged server-side only
- **Rate limiting ready**: Client information available for rate limiting
- **Input validation**: Pydantic schemas for all requests

---

## API Reference

### Request/Response DTOs

#### LoginDTO
```python
class LoginDTO(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Extended session duration")
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, max_length=45)
```

#### AuthResponseDTO
```python
class AuthResponseDTO(BaseModel):
    user: UserResponseDTO
    session: SessionResponseDTO
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
```

#### LogoutDTO
```python
class LogoutDTO(BaseModel):
    revoke_all_sessions: bool = Field(False, description="Revoke all user sessions")
```

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid email or password",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

#### 403 Forbidden
```json
{
  "detail": "Permission required: user:write"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Authentication service temporarily unavailable"
}
```

---

## Integration Examples

### FastAPI Route Protection

```python
from fastapi import APIRouter, Depends
from src.iam.presentation.dependencies.jwt_dependencies import (
    require_permission, require_role, JWTAuth
)

router = APIRouter()

# Public endpoint
@router.get("/health")
def health_check():
    return {"status": "healthy"}

# Authenticated endpoint
@router.get("/profile")
def get_profile(auth = JWTAuth):
    return {
        "user_id": auth.user_id,
        "email": auth.email,
        "organization": auth.organization_id
    }

# Permission-based endpoint
@router.get("/users")
def list_users(auth = require_permission("user:read")):
    # User must have "user:read" permission
    return {"users": get_all_users()}

# Role-based endpoint
@router.delete("/system/reset")
def reset_system(auth = require_role("super_admin")):
    # User must have "super_admin" role
    return {"reset": True}

# Multiple permission options
@router.post("/reports")
def create_report(auth = require_any_permission("report:create", "admin:*")):
    # User needs either "report:create" OR "admin:*" permission
    return {"report_id": create_new_report()}

# Organization-scoped endpoint
@router.get("/org/settings")
def get_org_settings(auth = JWTAuthWithOrg):
    # Ensures organization context is present
    return get_organization_settings(auth.organization_id)
```

### Custom Authorization Logic

```python
@router.post("/users/{user_id}/promote")
def promote_user(
    user_id: str,
    auth = JWTAuth
):
    # Custom authorization logic
    if not auth.has_permission("user:promote"):
        if not (auth.has_role("manager") and 
                auth.has_permission("user:read")):
            raise HTTPException(403, "Insufficient permissions")
    
    # Check organization context
    if auth.organization_id != get_user_organization(user_id):
        raise HTTPException(403, "Cross-organization access denied")
    
    return promote_user_to_admin(user_id)
```

### Multi-Tenant Context Usage

```python
@router.get("/dashboard")
def get_dashboard(auth = JWTAuthWithOrg):
    # Organization context guaranteed to be present
    return {
        "organization": {
            "id": auth.organization_id,
            "name": get_organization_name(auth.organization_id)
        },
        "user_permissions": auth.permissions,
        "user_roles": auth.roles,
        "data": get_organization_dashboard_data(auth.organization_id)
    }
```

### Session Management

```python
@router.get("/sessions")
def list_user_sessions(auth = require_permission("session:read")):
    return {
        "sessions": get_user_sessions(auth.user_id),
        "current_session": get_current_session(auth.token_payload)
    }

@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    auth = require_permission("session:revoke")
):
    session = get_session_by_id(session_id)
    
    # Users can only revoke their own sessions (unless admin)
    if session.user_id != auth.user_id and not auth.has_role("admin"):
        raise HTTPException(403, "Can only revoke own sessions")
    
    revoke_session(session_id)
    return {"revoked": True}

@router.post("/sessions/revoke-all")
def revoke_all_sessions(auth = JWTAuth):
    count = revoke_all_user_sessions(auth.user_id)
    return {"revoked_count": count}
```

---

## Security Best Practices

### For Developers

1. **Always use HTTPS** in production
2. **Store JWT secret securely** - use environment variables, never hardcode
3. **Implement proper CORS** settings for your frontend domains
4. **Use short token lifespans** - 15 minutes is recommended
5. **Implement token refresh** - automatic refresh before expiration
6. **Log security events** - failed logins, unusual access patterns
7. **Validate all inputs** - use Pydantic schemas for request validation
8. **Handle errors securely** - don't expose internal information

### For Production

1. **Use RS256 algorithm** with proper public/private key pairs
2. **Implement rate limiting** on authentication endpoints
3. **Monitor session activity** - detect unusual patterns
4. **Set up log aggregation** for security events
5. **Use secure headers** - implement security middleware
6. **Regular secret rotation** - rotate JWT signing keys periodically
7. **Database security** - encrypt sensitive session data
8. **Network security** - use VPN/private networks for database access

### Token Management

```python
# Good: Short-lived tokens with refresh
access_token = create_access_token(
    user_id=user.id,
    expires_delta=timedelta(minutes=15)  # Short lifespan
)

# Good: Automatic refresh before expiration
if token_expires_in_minutes(token) < 5:
    new_token = refresh_token(token)
    update_client_token(new_token)

# Bad: Long-lived tokens
access_token = create_access_token(
    expires_delta=timedelta(days=30)  # Too long!
)
```

### Permission Design

```python
# Good: Granular permissions
permissions = [
    "user:read",
    "user:write", 
    "organization:read"
]

# Good: Hierarchical permissions with wildcards
permissions = [
    "admin:*",  # All admin permissions
    "report:read"
]

# Bad: Overly broad permissions
permissions = ["*:*"]  # Too permissive

# Good: Organization-scoped permissions
@router.get("/org-users")
def get_org_users(auth = JWTAuthWithOrg):
    # Automatically scoped to user's organization
    return get_users_in_organization(auth.organization_id)
```

### Error Handling

```python
# Good: Generic error messages for security
try:
    user = authenticate(email, password)
except InvalidCredentialsError:
    raise HTTPException(401, "Invalid email or password")
except UserInactiveError:
    raise HTTPException(401, "Invalid email or password")  # Same message

# Bad: Specific error messages that reveal information
try:
    user = authenticate(email, password)
except UserNotFoundError:
    raise HTTPException(401, "User not found")  # Reveals user existence
except InvalidPasswordError:
    raise HTTPException(401, "Wrong password")  # Confirms user exists
```

---

This documentation provides a comprehensive guide to the JWT + Session authentication system, covering all aspects from basic usage to advanced security considerations. The system is designed to be both performant and secure, suitable for enterprise multi-tenant applications.