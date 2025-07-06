# RAG Integration with Document Permissions

This document explains how RAG (Retrieval-Augmented Generation) integration changes and enhances the document permission system to work seamlessly across multiple applications (management_app, web_chat_app, whatsapp_app).

## 🎯 **Key Changes for RAG Integration**

### **1. Enhanced Vector Metadata with Permission Context**

RAG systems now store comprehensive permission metadata with each vector embedding:

```python
# Vector metadata includes full permission context
vector_metadata = {
    "document_id": "uuid",
    "chunk_id": "doc_uuid_chunk_0",
    "organization_id": "org_uuid",
    "owner_id": "user_uuid",
    
    # Permission context for fast filtering
    "shared_with_roles": ["RH", "DP"],
    "shared_with_users": ["user1", "user2"],
    "confidentiality_level": "internal",
    "ai_query_enabled": True,
    "training_enabled": False,
    
    # Application access control
    "accessible_via": ["management_app", "web_chat_app", "whatsapp_app"],
    
    # Performance optimization
    "permission_hash": "abc123",  # For cache invalidation
    "priority_score": 0.8,
    "content_type": "policy"
}
```

### **2. Permission-Aware Vector Search**

RAG queries now include permission filters before semantic search:

```python
# Example: User with "RH" role searching for vacation policy
rag_search = permission_aware_search.search_with_permissions(
    user_id=user_id,
    organization_id=org_id,
    query="What is the vacation policy?",
    application_context="web_chat_app"
)

# Only returns chunks from documents user can access
accessible_chunks = rag_search.results
```

### **3. Multi-Application Consistency**

All applications (management_app, chat apps) use identical permission enforcement:

```python
# Management app RAG search
mgmt_results = rag_service.search_documents(
    query="company policies",
    user_id=admin_user_id,
    app_context="management_app"  # Admin gets broader access
)

# Web chat RAG search  
chat_results = rag_service.search_documents(
    query="company policies", 
    user_id=regular_user_id,
    app_context="web_chat_app"  # Filtered by user permissions
)

# WhatsApp chat RAG search
whatsapp_results = rag_service.search_documents(
    query="company policies",
    user_id=regular_user_id, 
    app_context="whatsapp_app"  # Same filtering as web chat
)
```

## 🏗️ **New Architecture Components**

### **1. Enhanced ChatDocumentAuthorizationService**

Extended with RAG-specific methods:

```python
# Bulk permission checking for RAG
accessible_docs = chat_auth_service.bulk_check_document_permissions(
    user_id=user_id,
    document_ids=[doc1, doc2, doc3],
    action="ai_query"
)

# Vector metadata creation
vector_metadata = chat_auth_service.create_vector_metadata_for_document(
    document_id=doc_id,
    document_resource=resource,
    chunk_id="chunk_0"
)

# Filter vector search results
filtered_results = chat_auth_service.filter_vector_search_results(
    user_id=user_id,
    search_results=raw_vector_results
)
```

### **2. RAGPermissionService**

Specialized service for RAG operations:

```python
# Permission-aware vector query building
vector_query = rag_permission_service.create_permission_aware_vector_query(
    user_id=user_id,
    organization_id=org_id,
    query="vacation policy",
    application_context="web_chat_app"
)

# Bulk validation of document chunks
accessible_chunks, denied_reasons = rag_permission_service.validate_rag_document_access(
    user_id=user_id,
    document_chunks=ai_retrieved_chunks,
    application_context="web_chat_app"
)
```

### **3. VectorMetadata Entity**

Comprehensive metadata model with permission context:

```python
# Create metadata from document resource
metadata = VectorMetadata.create_from_document_resource(
    document_id=doc_id,
    chunk_id="chunk_0",
    chunk_index=0,
    chunk_text="Employee vacation policy...",
    document_resource=doc_resource
)

# Fast permission check using metadata only
can_access = metadata.can_user_access(
    user_id=str(user_id),
    user_roles=["RH", "member"],
    user_clearance_level="internal",
    application_context=ApplicationContext.WEB_CHAT_APP
)
```

### **4. BulkPermissionService**

Optimized for high-performance RAG operations:

```python
# Efficient bulk permission checking
request = BulkPermissionRequest(
    user_id=user_id,
    organization_id=org_id,
    document_ids=large_document_list,
    action="ai_query"
)

result = bulk_permission_service.bulk_check_document_permissions(request)
# Returns: permissions, cached_results, computed_results, execution_time
```

### **5. PermissionAwareVectorSearch**

Complete vector search with permission integration:

```python
# Search with automatic permission filtering
search_result = vector_search.search_with_permissions(
    user_id=user_id,
    organization_id=org_id,
    query="employee benefits",
    application_context="web_chat_app",
    max_results=10
)

# Search within specific documents only
document_specific_search = vector_search.search_by_document_ids(
    user_id=user_id,
    organization_id=org_id,
    document_ids=[hr_manual_id, policy_doc_id],
    query="vacation days"
)

# Search by content type
faq_results = vector_search.search_by_content_type(
    user_id=user_id,
    organization_id=org_id,
    content_types=["faq", "policy"],
    query="how to request time off"
)
```

### **6. PermissionChangeEventService**

Real-time vector metadata updates:

```python
# Document permission change triggers vector update
await event_service.emit_document_permission_change(
    change_type=PermissionChangeType.ROLE_SHARING_UPDATED,
    document_id=doc_id,
    organization_id=org_id,
    changed_by_user_id=admin_id,
    old_resource=old_doc_resource,
    new_resource=updated_doc_resource
)

# User role change affects accessible documents
await event_service.emit_user_role_change(
    user_id=user_id,
    organization_id=org_id,
    old_roles=["member"],
    new_roles=["member", "RH"],
    changed_by_user_id=admin_id
)
```

## 📊 **Performance Optimizations**

### **1. Two-Tier Permission Filtering**

1. **Fast Metadata Filtering**: Uses vector metadata for quick permission checks
2. **Full Authorization Fallback**: Uses authorization service for complex cases

```python
# Fast path: metadata-only filtering
if use_metadata_filtering:
    filtered_results = self._filter_by_metadata(user_id, raw_results)
else:
    # Slower but more accurate: full authorization checks
    filtered_results = self._filter_by_full_permission_check(user_id, raw_results)
```

### **2. Permission Caching**

```python
# Cache user permissions for RAG queries
cached_permissions = bulk_service.precompute_user_permissions(
    user_id=user_id,
    organization_id=org_id,
    document_ids=frequently_accessed_docs,
    actions=["ai_query", "read"],
    application_contexts=["web_chat_app", "whatsapp_app"]
)
```

### **3. Batch Processing**

```python
# Process large document lists in batches
accessible_docs = bulk_service.filter_accessible_documents(
    user_id=user_id,
    organization_id=org_id,
    document_ids=all_organization_docs,  # Could be thousands
    batch_size=100  # Process in manageable chunks
)
```

## 🔄 **Multi-Application Integration Flow**

### **Complete RAG Flow Across Applications**

```python
# 1. User uploads document in management_app
document_resource = create_document_resource(
    title="Employee Handbook",
    owner_id=admin_id,
    shared_with_roles=["RH", "manager"],
    ai_query_enabled=True
)

# 2. Document gets chunked and vectorized with permissions
for chunk_index, chunk_text in enumerate(document_chunks):
    vector_metadata = create_vector_metadata_for_document(
        document_id=doc_id,
        chunk_id=f"{doc_id}_chunk_{chunk_index}",
        chunk_text=chunk_text,
        document_resource=document_resource
    )
    
    # Store vector embedding with metadata
    vector_store.index(
        text=chunk_text,
        metadata=vector_metadata.to_vector_store_metadata()
    )

# 3. User queries in web_chat_app
chat_query = "What is the dress code policy?"
accessible_chunks = permission_aware_search.search_with_permissions(
    user_id=employee_id,
    organization_id=org_id,
    query=chat_query,
    application_context="web_chat_app"
)

# 4. AI generates response using only accessible chunks
ai_response = generate_response(
    query=chat_query,
    context_chunks=accessible_chunks.results,
    user_permissions=accessible_chunks.user_context
)

# 5. Same query in whatsapp_app gets identical permission filtering
whatsapp_chunks = permission_aware_search.search_with_permissions(
    user_id=employee_id,
    organization_id=org_id,
    query=chat_query,
    application_context="whatsapp_app"  # Same result as web_chat_app
)
```

## 🛡️ **Security Features**

### **1. Fail-Safe Design**
- Access denied by default if permissions unclear
- Graceful degradation on errors
- Comprehensive audit logging

### **2. Multi-Layer Security**
1. **Application-level**: Different permission contexts per app
2. **Vector-level**: Metadata-based filtering
3. **Document-level**: Full authorization service validation
4. **Chunk-level**: Granular access control per document section

### **3. Real-Time Permission Sync**
- Vector metadata updates when permissions change
- Cache invalidation on permission updates
- Event-driven architecture for consistency

## 🎯 **Benefits of RAG Integration**

1. **Consistent Security**: Same permission rules across all applications
2. **High Performance**: Optimized filtering with caching and batching
3. **Real-Time Updates**: Vector metadata stays in sync with permissions
4. **Scalable**: Handles large document collections efficiently
5. **Flexible**: Supports complex permission scenarios (roles, users, confidentiality)
6. **Auditable**: Complete permission change tracking
7. **Fail-Safe**: Secure by default with graceful error handling

This RAG integration ensures that your document permission system works seamlessly across all applications while maintaining security, performance, and consistency.