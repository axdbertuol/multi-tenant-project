# Microservices Integration Guide

This document explains how external microservices should integrate with the IAM and Plans bounded contexts for document permissions and AI training functionality.

## 🏗️ **Architecture Overview**

The system consists of these bounded contexts and external services:

### **Bounded Contexts (Internal)**
- **IAM**: User authentication, authorization, document permissions
- **Plans**: Subscription plans, resource limits, feature management

### **External Microservices**
- **Document Service**: Document CRUD operations, MINIO integration
- **Training Service**: AI model training with cronjobs
- **RAG Service**: Retrieval-Augmented Generation for chat responses
- **MINIO**: Object storage for document files

## 📋 **Integration Requirements**

### **Document Service Requirements**

The Document Service should implement these capabilities:

#### **1. Document CRUD Operations**
```python
# Upload document workflow
def upload_document(user_id, org_id, file_data, metadata):
    # 1. Validate upload with IAM
    validation = iam_gateway.validate_document_upload(
        user_id=user_id,
        organization_id=org_id,
        file_name=file_data.filename,
        file_size_mb=file_data.size / 1024 / 1024,
        file_format=file_data.extension,
        application_context="management_app"
    )
    
    if not validation["allowed"]:
        raise PermissionError(validation["reason"])
    
    # 2. Upload to MINIO
    minio_url = minio_client.upload(
        bucket=f"org-{org_id}",
        filename=file_data.filename,
        content=file_data.content
    )
    
    # 3. Register with IAM
    document_id = uuid4()
    iam_result = iam_gateway.create_document_in_iam(
        document_id=document_id,
        title=metadata.get("title", file_data.filename),
        owner_id=user_id,
        organization_id=org_id,
        document_metadata={
            "minio_url": minio_url,
            "file_format": file_data.extension,
            "file_size_mb": file_data.size / 1024 / 1024,
            "shared_with_roles": metadata.get("shared_with_roles", []),
            "ai_training_enabled": metadata.get("ai_training_enabled", True),
            "ai_query_enabled": metadata.get("ai_query_enabled", True),
            **metadata
        }
    )
    
    # 4. Store document record
    document = Document(
        id=document_id,
        filename=file_data.filename,
        minio_url=minio_url,
        owner_id=user_id,
        organization_id=org_id,
        **metadata
    )
    document_repository.save(document)
    
    return document
```

#### **2. Document Access Control**
```python
def get_document(user_id, document_id, action="read"):
    # 1. Validate access with IAM
    access_check = iam_gateway.validate_document_access(
        user_id=user_id,
        document_id=document_id,
        action=action,
        application_context="management_app"
    )
    
    if not access_check["allowed"]:
        raise PermissionError(access_check["reason"])
    
    # 2. Fetch document
    document = document_repository.find_by_id(document_id)
    if not document:
        raise NotFoundError("Document not found")
    
    # 3. Get file from MINIO
    file_content = minio_client.download(document.minio_url)
    
    # 4. Log access
    iam_gateway.log_external_service_access(
        user_id=user_id,
        service_type="document_service",
        action=action,
        resource_id=document_id,
        success=True
    )
    
    return file_content, document
```

#### **3. Required API Endpoints**
```python
# Document CRUD
POST   /documents/upload
GET    /documents/{document_id}
PUT    /documents/{document_id}
DELETE /documents/{document_id}
GET    /documents/organization/{org_id}

# Document sharing
POST   /documents/{document_id}/share
GET    /documents/{document_id}/permissions
PUT    /documents/{document_id}/permissions

# Bulk operations
POST   /documents/bulk/upload
GET    /documents/bulk/download
POST   /documents/bulk/permissions
```

### **Training Service Requirements**

The Training Service should implement these capabilities:

#### **1. Scheduled Training Jobs**
```python
@cron("0 2 * * *")  # Daily at 2 AM
def train_updated_documents():
    # 1. Get all organizations
    organizations = get_all_organizations()
    
    for org in organizations:
        # 2. Get updated documents since last training
        updated_docs = document_service.get_updated_documents(
            organization_id=org.id,
            since=last_training_time
        )
        
        if not updated_docs:
            continue
            
        # 3. Get admin user for permission checks
        admin_user = get_organization_admin(org.id)
        
        # 4. Filter documents available for training
        training_result = iam_gateway.get_accessible_documents_for_training(
            user_id=admin_user.id,
            organization_id=org.id,
            document_ids=[doc.id for doc in updated_docs]
        )
        
        accessible_docs = training_result["accessible_documents"]
        
        if not accessible_docs:
            continue
        
        # 5. Download and process documents
        training_data = []
        for doc_id in accessible_docs:
            doc_content, doc_metadata = document_service.get_document(
                user_id=admin_user.id,
                document_id=doc_id,
                action="train"
            )
            training_data.append({
                "id": doc_id,
                "content": doc_content,
                "metadata": doc_metadata
            })
        
        # 6. Train model
        model_version = train_organization_model(
            organization_id=org.id,
            training_data=training_data
        )
        
        # 7. Update model registry
        model_registry.update_organization_model(
            organization_id=org.id,
            model_version=model_version,
            trained_on=accessible_docs
        )
```

#### **2. Permission-Aware Training**
```python
def train_organization_model(organization_id, training_data):
    # 1. Get organization integration settings
    settings = iam_gateway.get_organization_integration_settings(organization_id)
    ai_settings = settings["ai_settings"]
    
    # 2. Configure training based on permissions
    training_config = {
        "auto_chunking": ai_settings["auto_chunking"],
        "semantic_search": ai_settings["semantic_search"],
        "content_filtering": ai_settings["content_filtering"],
        "organization_id": str(organization_id)
    }
    
    # 3. Process documents with permission metadata
    processed_chunks = []
    for doc_data in training_data:
        # Extract permission context for each document
        chunks = chunk_document(doc_data["content"], training_config)
        
        for chunk in chunks:
            chunk["permission_metadata"] = {
                "document_id": doc_data["id"],
                "organization_id": organization_id,
                "training_allowed": True,
                "access_controls": doc_data["metadata"].get("access_controls", {})
            }
            processed_chunks.append(chunk)
    
    # 4. Train model with permission-aware chunks
    model = train_model(processed_chunks, training_config)
    
    return model
```

#### **3. Required API Endpoints**
```python
# Training management
POST   /training/organizations/{org_id}/trigger
GET    /training/organizations/{org_id}/status
GET    /training/organizations/{org_id}/history

# Model management
GET    /models/organizations/{org_id}/current
GET    /models/organizations/{org_id}/versions
POST   /models/organizations/{org_id}/deploy
```

### **RAG Service Requirements**

The RAG Service should implement these capabilities:

#### **1. Permission-Aware Vector Search**
```python
def query_documents(user_id, organization_id, query, application_context="web_chat_app"):
    # 1. Get query context from IAM
    query_context = iam_gateway.get_rag_query_context(
        user_id=user_id,
        organization_id=organization_id,
        query=query,
        application_context=application_context
    )
    
    if not query_context["allowed"]:
        raise PermissionError("User not authorized for AI queries")
    
    # 2. Build permission-aware vector search
    search_filters = query_context["filters"]
    user_context = query_context["user_context"]
    
    # 3. Search vector database with filters
    search_results = vector_db.search(
        query=query,
        filters={
            "organization_id": search_filters["organization_id"],
            "ai_query_enabled": True,
            "application_context": application_context,
            # Additional permission filters based on user context
            **build_permission_filters(user_context)
        },
        limit=10
    )
    
    # 4. Validate each result with IAM (if needed)
    validated_results = []
    for result in search_results:
        doc_id = result.metadata.get("document_id")
        
        # Quick validation using metadata
        if quick_permission_check(user_context, result.metadata):
            validated_results.append(result)
        else:
            # Full validation for complex cases
            access_check = iam_gateway.validate_document_access(
                user_id=user_id,
                document_id=doc_id,
                action="ai_query",
                application_context=application_context
            )
            
            if access_check["allowed"]:
                validated_results.append(result)
    
    # 5. Generate response
    response = generate_ai_response(query, validated_results, user_context)
    
    # 6. Log query
    iam_gateway.log_external_service_access(
        user_id=user_id,
        service_type="rag_service",
        action="query",
        success=True,
        additional_context={
            "query": query,
            "results_count": len(validated_results),
            "application": application_context
        }
    )
    
    return response
```

#### **2. Vector Metadata Management**
```python
def index_document_for_rag(document_id, document_content, document_metadata):
    # 1. Get permission metadata from IAM
    iam_resource = iam_gateway.get_document_resource(document_id)
    
    # 2. Chunk document
    chunks = chunk_document(document_content)
    
    # 3. Create embeddings with permission metadata
    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk.text)
        
        # Include permission context in vector metadata
        vector_metadata = {
            "document_id": str(document_id),
            "chunk_id": f"{document_id}_chunk_{i}",
            "organization_id": str(document_metadata["organization_id"]),
            "owner_id": str(document_metadata["owner_id"]),
            
            # Permission context
            "shared_with_roles": iam_resource.get("shared_with_roles", []),
            "shared_with_users": iam_resource.get("shared_with_users", []),
            "confidentiality_level": iam_resource.get("confidentiality_level", "public"),
            "ai_query_enabled": iam_resource.get("ai_query_enabled", True),
            
            # Content metadata
            "title": document_metadata.get("title", ""),
            "tags": document_metadata.get("tags", []),
            "created_at": document_metadata.get("created_at", "")
        }
        
        # 4. Index in vector database
        vector_db.index(
            vector=embedding,
            metadata=vector_metadata,
            namespace=f"org_{document_metadata['organization_id']}"
        )
```

#### **3. Required API Endpoints**
```python
# RAG queries
POST   /rag/query
POST   /rag/chat/{session_id}
GET    /rag/chat/{session_id}/history

# Document indexing
POST   /rag/documents/{document_id}/index
DELETE /rag/documents/{document_id}/unindex
POST   /rag/documents/bulk/reindex

# Vector management
GET    /rag/vectors/stats
POST   /rag/vectors/search
DELETE /rag/vectors/organization/{org_id}
```

### **MINIO Integration Requirements**

#### **1. Bucket Organization**
```python
# Bucket structure
org-{organization_id}/
├── documents/
│   ├── {document_id}/
│   │   ├── original.{ext}
│   │   ├── processed.json
│   │   └── chunks/
│   │       ├── chunk_0.txt
│   │       └── chunk_1.txt
├── models/
│   ├── {model_version}/
│   │   ├── model.bin
│   │   └── metadata.json
└── vectors/
    └── {document_id}/
        └── embeddings.json
```

#### **2. Access Control**
```python
def configure_minio_bucket(organization_id):
    bucket_name = f"org-{organization_id}"
    
    # Create bucket if not exists
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    # Set bucket policy for organization access
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": f"arn:aws:iam::{organization_id}:*"},
                "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            }
        ]
    }
    
    minio_client.set_bucket_policy(bucket_name, json.dumps(bucket_policy))
```

## 🔌 **Integration APIs**

### **IAM External API Gateway**

The IAM service provides these APIs for external services:

```python
# Document validation
POST /external/documents/validate-upload
POST /external/documents/validate-access
POST /external/documents/create-in-iam

# Training integration
POST /external/training/get-accessible-documents
POST /external/training/validate-access

# RAG integration  
POST /external/rag/get-query-context
POST /external/rag/validate-query

# General integration
POST /external/services/validate-access
POST /external/services/log-access
GET  /external/organizations/{org_id}/settings
GET  /external/health
```

### **Plans Service Integration**

External services should query Plans service for:

```python
# Resource limits
GET /plans/organizations/{org_id}/document-limits
GET /plans/organizations/{org_id}/features

# Usage tracking
POST /plans/organizations/{org_id}/usage/documents
POST /plans/organizations/{org_id}/usage/ai-queries
POST /plans/organizations/{org_id}/usage/training
```

## 🔐 **Security Considerations**

### **1. Service Authentication**
```python
# Each external service should authenticate with IAM
headers = {
    "Authorization": f"Bearer {service_jwt_token}",
    "X-Service-Name": "document_service",
    "X-Service-Version": "1.0.0"
}
```

### **2. Rate Limiting**
```python
# Implement rate limiting per organization
@rate_limit("100/hour", key=lambda: f"org_{request.org_id}")
def upload_document():
    pass
```

### **3. Audit Logging**
```python
# All services should log access attempts
def log_access(user_id, action, resource_id, success, details):
    audit_log.info({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": str(user_id),
        "action": action,
        "resource_id": str(resource_id) if resource_id else None,
        "success": success,
        "service": "document_service",
        "details": details
    })
```

## 📊 **Monitoring and Health Checks**

### **1. Health Check Endpoints**
```python
# Each service should provide health checks
GET /health
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "dependencies": {
        "iam_service": "healthy",
        "plans_service": "healthy", 
        "minio": "healthy",
        "database": "healthy"
    }
}
```

### **2. Metrics Collection**
```python
# Track key metrics
metrics = {
    "documents_uploaded": Counter("documents_uploaded_total"),
    "ai_queries_processed": Counter("ai_queries_total"),
    "training_jobs_completed": Counter("training_jobs_total"),
    "permission_checks": Histogram("permission_check_duration_seconds"),
    "document_access_denied": Counter("document_access_denied_total")
}
```

## 🚀 **Deployment Considerations**

### **1. Service Discovery**
```yaml
# docker-compose.yml
services:
  iam-service:
    image: iam-service:latest
    environment:
      - DATABASE_URL=postgresql://...
      - JWT_SECRET=...
    
  document-service:
    image: document-service:latest
    environment:
      - IAM_SERVICE_URL=http://iam-service:8000
      - MINIO_URL=http://minio:9000
    depends_on:
      - iam-service
      - minio
  
  training-service:
    image: training-service:latest
    environment:
      - IAM_SERVICE_URL=http://iam-service:8000
      - DOCUMENT_SERVICE_URL=http://document-service:8001
    depends_on:
      - iam-service
      - document-service
```

### **2. Environment Configuration**
```python
# Environment variables for external services
IAM_SERVICE_URL=http://iam-service:8000
PLANS_SERVICE_URL=http://plans-service:8002
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=minioaccess
MINIO_SECRET_KEY=miniosecret

# Service-specific configuration
DOCUMENT_SERVICE_MAX_FILE_SIZE=50MB
TRAINING_SERVICE_CRON_SCHEDULE=0 2 * * *
RAG_SERVICE_MAX_QUERY_LENGTH=1000
```

This integration guide ensures that all external microservices can properly integrate with the IAM and Plans bounded contexts while maintaining security, permissions, and proper separation of concerns.