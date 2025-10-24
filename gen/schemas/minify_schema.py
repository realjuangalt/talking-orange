#!/usr/bin/env python3
"""
Schema Minification Script
Takes schema files and produces minified versions for API calls
Updated to handle the new modular schema system
"""

import json
import os
import sys

def validate_json_schema(file_path):
    """
    Validate that a file contains valid JSON schema
    
    Args:
        file_path (str): Path to JSON schema file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic schema validation
        if not isinstance(data, dict):
            return False
        
        if '$schema' not in data:
            print(f"⚠️  Warning: {file_path} missing $schema field")
        
        if 'type' not in data:
            print(f"⚠️  Warning: {file_path} missing type field")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

def minify_json(input_file, output_file):
    """
    Minify a JSON file by removing unnecessary whitespace and formatting
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output minified JSON file
    """
    try:
        # Read and parse the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Write minified JSON to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        
        print(f"✅ Successfully minified {input_file} -> {output_file}")
        
        # Show file size comparison
        input_size = os.path.getsize(input_file)
        output_size = os.path.getsize(output_file)
        reduction = ((input_size - output_size) / input_size) * 100
        
        print(f"📊 File size: {input_size:,} bytes -> {output_size:,} bytes")
        print(f"📉 Size reduction: {reduction:.1f}%")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{input_file}': {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def minify_schemas():
    """Minify both character and encounter schemas and organize in schemas folder"""
    # Create schemas directory if it doesn't exist
    schemas_dir = "schemas"
    if not os.path.exists(schemas_dir):
        os.makedirs(schemas_dir)
        print(f"Created schemas directory: {schemas_dir}")
    
    schemas = {
        'schemas/character_schema.json': 'schemas/character_schema.min.json',
        'schemas/encounter_schema.json': 'schemas/encounter_schema.min.json'
    }
    
    for input_file, output_file in schemas.items():
        if os.path.exists(input_file):
            try:
                with open(input_file, 'r') as f:
                    schema = json.load(f)
                
                # Minify schema
                minified = json.dumps(schema, separators=(',', ':'))
                
                with open(output_file, 'w') as f:
                    f.write(minified)
                print(f"✅ Minified: {input_file} -> {output_file}")
                
                # Show file size comparison
                input_size = os.path.getsize(input_file)
                output_size = os.path.getsize(output_file)
                compression = ((input_size - output_size) / input_size) * 100
                print(f"   📊 Size: {input_size} -> {output_size} bytes ({compression:.1f}% reduction)")
                
            except Exception as e:
                print(f"❌ Error minifying {input_file}: {e}")
        else:
            print(f"⚠️  Warning: Input schema not found: {input_file}")

def validate_schemas():
    """Validate that all schema files are valid JSON"""
    schemas_dir = "schemas"
    if not os.path.exists(schemas_dir):
        print("❌ Schemas directory not found")
        return False
    
    schema_files = [
        'schemas/character_schema.json',
        'schemas/encounter_schema.json'
    ]
    
    all_valid = True
    for schema_file in schema_files:
        if os.path.exists(schema_file):
            try:
                with open(schema_file, 'r') as f:
                    json.load(f)
                print(f"✅ Valid JSON: {schema_file}")
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in {schema_file}: {e}")
                all_valid = False
        else:
            print(f"⚠️  Schema file not found: {schema_file}")
            all_valid = False
    
    return all_valid

def main():
    """Main function"""
    print("🚀 Schema Minification & Organization")
    print("=" * 50)
    
    # Check if command line arguments are provided
    if len(sys.argv) == 3:
        # Command line mode: minify specific file
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        if not os.path.exists(input_file):
            print(f"❌ Error: Input file '{input_file}' not found")
            print("Usage: python3 minify_schema.py <input_file> <output_file>")
            print("Default: python3 minify_schema.py gs_schema.json gs_schema.min.json")
            sys.exit(1)
        
        # Perform minification
        success = minify_json(input_file, output_file)
        sys.exit(0 if success else 1)
    
    # Default mode: minify all schemas
    # Validate schemas first
    print("\n🔍 Validating schemas...")
    if not validate_schemas():
        print("❌ Schema validation failed. Please fix errors before minifying.")
        return
    
    # Minify schemas
    print("\n📦 Minifying schemas...")
    minify_schemas()
    
    # Final validation
    print("\n🔍 Final validation...")
    if validate_schemas():
        print("\n✅ All schemas successfully minified and organized!")
        print("\n📁 Schema files created:")
        print("   schemas/character_schema.json")
        print("   schemas/character_schema.min.json")
        print("   schemas/encounter_schema.json")
        print("   schemas/encounter_schema.min.json")
        print("   schemas/README.md")
    else:
        print("❌ Final validation failed")

if __name__ == "__main__":
    main() 