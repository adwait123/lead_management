#!/usr/bin/env python3
"""
Fix Pydantic v1 compatibility - revert to from_orm and orm_mode
"""
import os
import re

def update_schemas_for_v1():
    """Update schemas.py for Pydantic v1 compatibility"""
    file_path = 'models/schemas.py'

    print(f"📝 Updating {file_path} for Pydantic v1...")

    with open(file_path, 'r') as f:
        content = f.read()

    # Replace from_attributes with orm_mode
    content = re.sub(r'from_attributes = True', 'orm_mode = True', content)

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("✅ Updated schemas.py for Pydantic v1")

def update_api_files_for_v1():
    """Update API files to use from_orm instead of model_validate"""
    api_files = []

    # Find all Python files in api directory
    for root, dirs, files in os.walk('api'):
        for file in files:
            if file.endswith('.py'):
                api_files.append(os.path.join(root, file))

    total_replacements = 0

    for file_path in api_files:
        print(f"📝 Updating {file_path}...")

        with open(file_path, 'r') as f:
            content = f.read()

        # Count and replace model_validate with from_orm
        original_count = content.count('.model_validate(')
        content = re.sub(r'\.model_validate\(', '.from_orm(', content)

        if original_count > 0:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Made {original_count} replacements")
            total_replacements += original_count
        else:
            print(f"   ➖ No changes needed")

    return total_replacements

def main():
    """Main function"""
    print("="*70)
    print("🔧 PYDANTIC V1 COMPATIBILITY FIX")
    print("="*70)
    print("Converting code back to Pydantic v1 syntax...")
    print()

    # Update schemas
    update_schemas_for_v1()

    # Update API files
    total_replacements = update_api_files_for_v1()

    print("\n" + "="*70)
    print("✅ PYDANTIC V1 COMPATIBILITY COMPLETED")
    print("="*70)
    print(f"Total .model_validate() → .from_orm() replacements: {total_replacements}")
    print()
    print("Changes made:")
    print("- schemas.py: from_attributes=True → orm_mode=True")
    print("- API files: .model_validate() → .from_orm()")
    print()
    print("Your staging server should now work with Pydantic v1.10.12!")

if __name__ == "__main__":
    main()