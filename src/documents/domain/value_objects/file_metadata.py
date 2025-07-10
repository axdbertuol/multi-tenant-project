from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class FileMetadata(BaseModel):
    """
    Value Object para metadados de arquivos.
    
    Contém informações sobre arquivos de documentos incluindo
    dados técnicos, processamento e indexação.
    """
    
    name: str = Field(..., description="Nome do arquivo")
    original_name: str = Field(..., description="Nome original do arquivo")
    size: int = Field(..., ge=0, description="Tamanho do arquivo em bytes")
    mime_type: str = Field(..., description="Tipo MIME do arquivo")
    extension: str = Field(..., description="Extensão do arquivo")
    checksum: str = Field(..., description="Hash SHA-256 do arquivo")
    encoding: Optional[str] = Field(None, description="Codificação do arquivo")
    
    # Metadados de processamento
    is_text_extractable: bool = Field(default=False, description="Se o texto pode ser extraído")
    is_searchable: bool = Field(default=False, description="Se o arquivo pode ser pesquisado")
    text_content_length: Optional[int] = Field(None, description="Tamanho do texto extraído")
    language: Optional[str] = Field(None, description="Idioma detectado no texto")
    
    # Tags e categorização
    tags: List[str] = Field(default_factory=list, description="Tags do arquivo")
    categories: List[str] = Field(default_factory=list, description="Categorias do arquivo")
    
    # Metadados específicos por tipo
    document_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados específicos de documentos")
    image_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados de imagens")
    video_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados de vídeos")
    
    model_config = {"frozen": True}
    
    @classmethod
    def create_from_file_info(
        cls,
        name: str,
        original_name: str,
        size: int,
        mime_type: str,
        checksum: str,
        **kwargs
    ) -> "FileMetadata":
        """Cria metadados a partir das informações básicas do arquivo."""
        extension = Path(original_name).suffix.lower()
        
        return cls(
            name=name,
            original_name=original_name,
            size=size,
            mime_type=mime_type,
            extension=extension,
            checksum=checksum,
            **kwargs
        )
    
    def get_file_type_category(self) -> str:
        """Retorna a categoria do tipo de arquivo."""
        if self.is_document():
            return "document"
        elif self.is_image():
            return "image"
        elif self.is_video():
            return "video"
        elif self.is_audio():
            return "audio"
        elif self.is_archive():
            return "archive"
        elif self.is_code():
            return "code"
        else:
            return "other"
    
    def is_document(self) -> bool:
        """Verifica se é um documento."""
        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/rtf",
            "application/rtf"
        ]
        return self.mime_type in document_types
    
    def is_image(self) -> bool:
        """Verifica se é uma imagem."""
        return self.mime_type.startswith("image/")
    
    def is_video(self) -> bool:
        """Verifica se é um vídeo."""
        return self.mime_type.startswith("video/")
    
    def is_audio(self) -> bool:
        """Verifica se é um áudio."""
        return self.mime_type.startswith("audio/")
    
    def is_archive(self) -> bool:
        """Verifica se é um arquivo compactado."""
        archive_types = [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
            "application/gzip",
            "application/x-tar"
        ]
        return self.mime_type in archive_types
    
    def is_code(self) -> bool:
        """Verifica se é um arquivo de código."""
        code_extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".php", ".rb", ".go"]
        return self.extension in code_extensions or self.mime_type.startswith("text/")
    
    def get_size_formatted(self) -> str:
        """Retorna o tamanho formatado em unidades legíveis."""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def is_large_file(self, threshold_mb: int = 100) -> bool:
        """Verifica se é um arquivo grande."""
        threshold_bytes = threshold_mb * 1024 * 1024
        return self.size > threshold_bytes
    
    def can_be_previewed(self) -> bool:
        """Verifica se o arquivo pode ter preview."""
        previewable_types = [
            "application/pdf",
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/json"
        ]
        return (
            self.mime_type in previewable_types or
            self.is_image() or
            (self.is_code() and self.size < 1024 * 1024)  # Código até 1MB
        )
    
    def requires_virus_scan(self) -> bool:
        """Verifica se requer escaneamento de vírus."""
        # Arquivos executáveis e arquivos compactados requerem scan
        dangerous_types = [
            "application/x-executable",
            "application/x-msdownload",
            "application/vnd.microsoft.portable-executable"
        ]
        return (
            self.mime_type in dangerous_types or
            self.is_archive() or
            self.extension in [".exe", ".bat", ".cmd", ".scr", ".com"]
        )
    
    def get_processing_requirements(self) -> List[str]:
        """Retorna lista de processamentos necessários."""
        requirements = []
        
        if self.is_document():
            requirements.append("text_extraction")
            requirements.append("indexing")
        
        if self.is_image():
            requirements.append("thumbnail_generation")
            requirements.append("metadata_extraction")
        
        if self.is_video():
            requirements.append("thumbnail_generation")
            requirements.append("metadata_extraction")
        
        if self.requires_virus_scan():
            requirements.append("virus_scan")
        
        if self.can_be_previewed():
            requirements.append("preview_generation")
        
        return requirements
    
    def add_tag(self, tag: str) -> "FileMetadata":
        """Adiciona uma tag."""
        if tag not in self.tags:
            new_tags = self.tags + [tag]
            return self.model_copy(update={"tags": new_tags})
        return self
    
    def remove_tag(self, tag: str) -> "FileMetadata":
        """Remove uma tag."""
        if tag in self.tags:
            new_tags = [t for t in self.tags if t != tag]
            return self.model_copy(update={"tags": new_tags})
        return self
    
    def add_category(self, category: str) -> "FileMetadata":
        """Adiciona uma categoria."""
        if category not in self.categories:
            new_categories = self.categories + [category]
            return self.model_copy(update={"categories": new_categories})
        return self
    
    def get_search_keywords(self) -> List[str]:
        """Retorna palavras-chave para busca."""
        keywords = []
        
        # Nome do arquivo sem extensão
        name_without_ext = Path(self.original_name).stem
        keywords.extend(name_without_ext.split())
        
        # Tags e categorias
        keywords.extend(self.tags)
        keywords.extend(self.categories)
        
        # Tipo de arquivo
        keywords.append(self.get_file_type_category())
        keywords.append(self.extension.replace(".", ""))
        
        return list(set(keywords))
    
    def is_similar_to(self, other: "FileMetadata") -> bool:
        """Verifica se é similar a outro arquivo."""
        return (
            self.checksum == other.checksum or
            (self.original_name == other.original_name and self.size == other.size)
        )