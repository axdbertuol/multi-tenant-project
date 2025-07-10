from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re
from pathlib import Path


class FolderPath(BaseModel):
    """
    Value Object para caminhos de pastas de documentos.
    
    Garante que os caminhos sejam válidos e consistentes
    dentro do sistema de documentos.
    """
    
    path: str = Field(..., description="Caminho da pasta")
    
    model_config = {"frozen": True}
    
    @validator('path')
    def validate_path(cls, v):
        """Valida o formato do caminho."""
        if not v:
            raise ValueError("Path cannot be empty")
        
        # Deve começar com /documents/
        if not v.startswith("/documents/"):
            raise ValueError("Path must start with /documents/")
        
        # Não deve conter caracteres inválidos
        invalid_chars = ["<", ">", ":", "\"", "|", "?", "*"]
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Path contains invalid characters: {invalid_chars}")
        
        # Não deve ter espaços no início/fim ou barras duplas
        if v != v.strip() or "//" in v:
            raise ValueError("Path cannot have leading/trailing spaces or double slashes")
        
        # Não deve terminar com barra (exceto raiz)
        if v.endswith("/") and v != "/documents/":
            raise ValueError("Path cannot end with slash (except root)")
        
        return v
    
    @classmethod
    def create_root(cls) -> "FolderPath":
        """Cria o caminho raiz dos documentos."""
        return cls(path="/documents")
    
    @classmethod
    def create_from_segments(cls, segments: List[str]) -> "FolderPath":
        """Cria um caminho a partir de segmentos."""
        if not segments:
            return cls.create_root()
        
        # Limpar e validar segmentos
        clean_segments = []
        for segment in segments:
            segment = segment.strip()
            if segment and segment != "documents":
                # Validar caracteres do segmento
                if not cls._is_valid_segment(segment):
                    raise ValueError(f"Invalid path segment: {segment}")
                clean_segments.append(segment)
        
        if not clean_segments:
            return cls.create_root()
        
        path = "/documents/" + "/".join(clean_segments)
        return cls(path=path)
    
    @classmethod
    def create_child_path(cls, parent_path: "FolderPath", child_name: str) -> "FolderPath":
        """Cria um caminho filho a partir de um caminho pai."""
        if not cls._is_valid_segment(child_name):
            raise ValueError(f"Invalid child name: {child_name}")
        
        if parent_path.is_root():
            new_path = f"/documents/{child_name}"
        else:
            new_path = f"{parent_path.path}/{child_name}"
        
        return cls(path=new_path)
    
    @staticmethod
    def _is_valid_segment(segment: str) -> bool:
        """Valida um segmento de caminho."""
        if not segment or not segment.strip():
            return False
        
        # Não deve conter caracteres inválidos
        invalid_chars = ["<", ">", ":", "\"", "|", "?", "*", "/", "\\"]
        if any(char in segment for char in invalid_chars):
            return False
        
        # Não deve começar ou terminar com ponto
        if segment.startswith(".") or segment.endswith("."):
            return False
        
        # Não deve ser nome reservado
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", 
                         "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", 
                         "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", 
                         "LPT7", "LPT8", "LPT9"]
        if segment.upper() in reserved_names:
            return False
        
        return True
    
    def get_segments(self) -> List[str]:
        """Retorna os segmentos do caminho."""
        if self.is_root():
            return []
        
        # Remove /documents/ e divide por /
        relative_path = self.path.replace("/documents/", "", 1)
        return relative_path.split("/") if relative_path else []
    
    def get_parent_path(self) -> Optional["FolderPath"]:
        """Retorna o caminho pai."""
        if self.is_root():
            return None
        
        segments = self.get_segments()
        if len(segments) <= 1:
            return FolderPath.create_root()
        
        parent_segments = segments[:-1]
        return FolderPath.create_from_segments(parent_segments)
    
    def get_name(self) -> str:
        """Retorna o nome da pasta (último segmento)."""
        if self.is_root():
            return "documents"
        
        segments = self.get_segments()
        return segments[-1] if segments else "documents"
    
    def get_depth(self) -> int:
        """Retorna a profundidade do caminho."""
        return len(self.get_segments())
    
    def is_root(self) -> bool:
        """Verifica se é o caminho raiz."""
        return self.path in ["/documents", "/documents/"]
    
    def is_child_of(self, parent: "FolderPath") -> bool:
        """Verifica se é filho de outro caminho."""
        if parent.is_root():
            return not self.is_root()
        
        return self.path.startswith(parent.path + "/")
    
    def is_parent_of(self, child: "FolderPath") -> bool:
        """Verifica se é pai de outro caminho."""
        return child.is_child_of(self)
    
    def is_ancestor_of(self, descendant: "FolderPath") -> bool:
        """Verifica se é ancestral de outro caminho."""
        return self.is_parent_of(descendant)
    
    def get_common_ancestor(self, other: "FolderPath") -> "FolderPath":
        """Retorna o ancestral comum mais próximo."""
        my_segments = self.get_segments()
        other_segments = other.get_segments()
        
        common_segments = []
        min_length = min(len(my_segments), len(other_segments))
        
        for i in range(min_length):
            if my_segments[i] == other_segments[i]:
                common_segments.append(my_segments[i])
            else:
                break
        
        return FolderPath.create_from_segments(common_segments)
    
    def get_relative_path_to(self, target: "FolderPath") -> str:
        """Retorna o caminho relativo até outro caminho."""
        if not target.is_child_of(self):
            raise ValueError("Target path is not a child of this path")
        
        return target.path.replace(self.path + "/", "", 1)
    
    def join(self, *segments: str) -> "FolderPath":
        """Junta segmentos ao caminho atual."""
        if not segments:
            return self
        
        current_segments = self.get_segments()
        new_segments = current_segments + list(segments)
        return FolderPath.create_from_segments(new_segments)
    
    def normalize(self) -> "FolderPath":
        """Normaliza o caminho removendo elementos redundantes."""
        segments = self.get_segments()
        normalized_segments = []
        
        for segment in segments:
            if segment == "." or not segment:
                continue  # Ignorar . e segmentos vazios
            elif segment == "..":
                if normalized_segments:
                    normalized_segments.pop()  # Subir um nível
            else:
                normalized_segments.append(segment)
        
        return FolderPath.create_from_segments(normalized_segments)
    
    def matches_pattern(self, pattern: str) -> bool:
        """Verifica se o caminho combina com um padrão."""
        # Suporte para padrões simples com *
        import fnmatch
        return fnmatch.fnmatch(self.path, pattern)
    
    def get_all_parent_paths(self) -> List["FolderPath"]:
        """Retorna todos os caminhos pai até a raiz."""
        parents = []
        current = self.get_parent_path()
        
        while current:
            parents.append(current)
            current = current.get_parent_path()
        
        return parents
    
    def __str__(self) -> str:
        return self.path
    
    def __repr__(self) -> str:
        return f"FolderPath('{self.path}')"