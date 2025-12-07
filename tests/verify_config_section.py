import configparser
from src.core.context import Context

def test_resolve_section_config():
    # Setup
    ctx = Context()
    ctx.clear()
    
    # Mock Config
    # Context.load_config reads from a file, but we can populate the internal config object directly for unit testing logic
    ctx.config.add_section('SECTION')
    ctx.config.set('SECTION', 'Key', 'Value')
    
    # Test Resolution
    result = ctx.resolve("${SECTION.Key}")
    print(f"Resolving ${{SECTION.Key}}: {result}")
    assert result == "Value"
    
    # Test Case Insensitivity (ConfigParser default)
    result_lower = ctx.resolve("${SECTION.key}")
    print(f"Resolving ${{SECTION.key}}: {result_lower}")
    assert result_lower == "Value"
    
    # Test Fallback (Non-existent section)
    result_missing = ctx.resolve("${MISSING.Key}")
    print(f"Resolving ${{MISSING.Key}}: {result_missing}")
    assert result_missing == "${MISSING.Key}"

    print("Verification Passed!")

if __name__ == "__main__":
    test_resolve_section_config()
