"""
Schema Loader
Utility module for loading and validating JSON schemas from the schemas/ directory.
Ensures generated content conforms to expected data structures.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class SchemaLoader:
    """Loads and validates JSON schemas from the schemas directory."""
    
    def __init__(self, schemas_dir: str = None):
        """
        Initialize the schema loader.
        
        Args:
            schemas_dir: Path to the schemas directory
        """
        if schemas_dir is None:
            # Default to gen/schemas directory
            schemas_dir = os.path.join(os.path.dirname(__file__), "schemas")
        self.schemas_dir = Path(schemas_dir)
        self._cache = {}
        
        # Create schemas directory if it doesn't exist (optional, only needed if schemas are used)
        if not self.schemas_dir.exists():
            self.schemas_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Schemas directory created (empty): {self.schemas_dir}. Add schema .json files if needed.")
    
    def load_schema(self, filename: str) -> Dict[str, Any]:
        """
        Load a JSON schema from file.
        
        Args:
            filename: Name of the schema file
            
        Returns:
            Schema dictionary
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema file is invalid JSON
        """
        # Check cache first
        if filename in self._cache:
            return self._cache[filename]
        
        schema_path = self.schemas_dir / filename
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                self._cache[filename] = schema
                return schema
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in schema file {filename}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading schema {filename}: {str(e)}")
    
    def get_character_schema(self) -> Dict[str, Any]:
        """Get character schema."""
        return self.load_schema("character_schema.json")
    
    def get_character_schema_min(self) -> Dict[str, Any]:
        """Get minified character schema."""
        return self.load_schema("character_schema.min.json")
    
    def get_encounter_schema(self) -> Dict[str, Any]:
        """Get encounter schema."""
        return self.load_schema("encounter_schema.json")
    
    def get_encounter_schema_min(self) -> Dict[str, Any]:
        """Get minified encounter schema."""
        return self.load_schema("encounter_schema.min.json")
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validate data against a schema.
        
        Args:
            data: Data to validate
            schema: Schema to validate against
            
        Returns:
            True if valid, False otherwise
        """
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError:
            return False
    
    def validate_character_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate character data against character schema.
        
        Args:
            data: Character data to validate
            
        Returns:
            True if valid, False otherwise
        """
        schema = self.get_character_schema()
        return self.validate_data(data, schema)
    
    def validate_encounter_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate encounter data against encounter schema.
        
        Args:
            data: Encounter data to validate
            
        Returns:
            True if valid, False otherwise
        """
        schema = self.get_encounter_schema()
        return self.validate_data(data, schema)
    
    def get_validation_errors(self, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """
        Get detailed validation errors.
        
        Args:
            data: Data to validate
            schema: Schema to validate against
            
        Returns:
            List of validation error messages
        """
        errors = []
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            errors.append(str(e.message))
            for error in e.context:
                errors.append(f"  - {error.message}")
        return errors
    
    def get_character_validation_errors(self, data: Dict[str, Any]) -> List[str]:
        """
        Get character data validation errors.
        
        Args:
            data: Character data to validate
            
        Returns:
            List of validation error messages
        """
        schema = self.get_character_schema()
        return self.get_validation_errors(data, schema)
    
    def get_encounter_validation_errors(self, data: Dict[str, Any]) -> List[str]:
        """
        Get encounter data validation errors.
        
        Args:
            data: Encounter data to validate
            
        Returns:
            List of validation error messages
        """
        schema = self.get_encounter_schema()
        return self.get_validation_errors(data, schema)
    
    def get_schema_properties(self, schema: Dict[str, Any]) -> List[str]:
        """
        Get list of required properties from a schema.
        
        Args:
            schema: Schema dictionary
            
        Returns:
            List of required property names
        """
        return schema.get("required", [])
    
    def get_character_required_properties(self) -> List[str]:
        """Get required properties for character data."""
        schema = self.get_character_schema()
        return self.get_schema_properties(schema)
    
    def get_encounter_required_properties(self) -> List[str]:
        """Get required properties for encounter data."""
        schema = self.get_encounter_schema()
        return self.get_schema_properties(schema)
    
    def clear_cache(self):
        """Clear the schema cache."""
        self._cache.clear()
    
    def list_available_schemas(self) -> List[str]:
        """
        List all available schema files.
        
        Returns:
            List of schema filenames
        """
        return [f.name for f in self.schemas_dir.glob("*.json")]

# Global instance for easy access - lazy loaded
_schema_loader = None

def get_schema_loader():
    global _schema_loader
    if _schema_loader is None:
        _schema_loader = SchemaLoader()
    return _schema_loader

schema_loader = get_schema_loader()

# Convenience functions
def load_schema(filename: str) -> Dict[str, Any]:
    """Load a schema by filename."""
    return schema_loader.load_schema(filename)

def get_character_schema() -> Dict[str, Any]:
    """Get character schema."""
    return schema_loader.get_character_schema()

def get_character_schema_min() -> Dict[str, Any]:
    """Get minified character schema."""
    return schema_loader.get_character_schema_min()

def get_encounter_schema() -> Dict[str, Any]:
    """Get encounter schema."""
    return schema_loader.get_encounter_schema()

def get_encounter_schema_min() -> Dict[str, Any]:
    """Get minified encounter schema."""
    return schema_loader.get_encounter_schema_min()

def validate_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against a schema."""
    return schema_loader.validate_data(data, schema)

def validate_character_data(data: Dict[str, Any]) -> bool:
    """Validate character data against character schema."""
    return schema_loader.validate_character_data(data)

def validate_encounter_data(data: Dict[str, Any]) -> bool:
    """Validate encounter data against encounter schema."""
    return schema_loader.validate_encounter_data(data)

def get_validation_errors(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Get detailed validation errors."""
    return schema_loader.get_validation_errors(data, schema)

def get_character_validation_errors(data: Dict[str, Any]) -> List[str]:
    """Get character data validation errors."""
    return schema_loader.get_character_validation_errors(data)

def get_encounter_validation_errors(data: Dict[str, Any]) -> List[str]:
    """Get encounter data validation errors."""
    return schema_loader.get_encounter_validation_errors(data)
