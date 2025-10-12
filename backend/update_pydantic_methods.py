#!/usr/bin/env python3
"""
Script to safely replace from_orm with model_validate across the codebase
"""
import os
import re
import sys

def update_file(file_path):
    """Update a single file to replace from_orm with model_validate"""
    print(f"Updating {file_path}...")

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Count replacements
        original_count = content.count('.from_orm(')

        # Replace from_orm with model_validate
        updated_content = re.sub(r'\.from_orm\(', '.model_validate(', content)

        # Count after replacement
        new_count = updated_content.count('.model_validate(')
        replacements = original_count

        if replacements > 0:
            with open(file_path, 'w') as f:
                f.write(updated_content)
            print(f"   ✅ Made {replacements} replacements in {file_path}")
        else:
            print(f"   ➖ No changes needed in {file_path}")

        return replacements

    except Exception as e:
        print(f"   ❌ Error updating {file_path}: {str(e)}")
        return 0

def main():
    """Main function to update all Python files"""
    print("=" * 70)
    print("UPDATING PYDANTIC from_orm TO model_validate")
    print("=" * 70)

    # Find all Python files in the API directory
    api_files = []
    for root, dirs, files in os.walk('api'):
        for file in files:
            if file.endswith('.py'):
                api_files.append(os.path.join(root, file))

    total_replacements = 0
    updated_files = []

    for file_path in api_files:
        replacements = update_file(file_path)
        total_replacements += replacements
        if replacements > 0:
            updated_files.append(file_path)

    print("\n" + "=" * 70)
    print("UPDATE SUMMARY")
    print("=" * 70)
    print(f"Files checked: {len(api_files)}")
    print(f"Files updated: {len(updated_files)}")
    print(f"Total replacements: {total_replacements}")

    if updated_files:
        print("\nUpdated files:")
        for file_path in updated_files:
            print(f"  - {file_path}")

    print(f"\n{'✅ All updates completed successfully!' if total_replacements > 0 else '✅ No updates needed.'}")

    return total_replacements

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    total = main()
    sys.exit(0)