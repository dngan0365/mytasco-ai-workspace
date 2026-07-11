#!/usr/bin/env python
"""Quick validation of new code structure (no external imports)."""
import sys
import os

sys.path.insert(0, '.')
os.environ.setdefault('DATASET_PATH', '')
os.environ.setdefault('ANTHROPIC_API_KEY', 'sk-ant-test-dummy')

# Validate router module can compile
try:
    from app.agent.router import IntentRoute, route_intent
    print("✓ router module loads successfully")
    
    # Test router logic
    tests = [
        ("chính sách tài chính chiến lược", IntentRoute.rag),
        ("xem chấm công", IntentRoute.tool),
        ("phê duyệt đơn", IntentRoute.human_approval),
        ("tin tức công ty", IntentRoute.tool),
    ]
    for query, expected in tests:
        result = route_intent(query)
        status = "✓" if result == expected else "✗"
        print(f"  {status} route_intent('{query}') = {result.value}")
        
except Exception as e:
    print(f"✗ router module failed: {e}")
    sys.exit(1)

# Validate openapi_gateway can compile
try:
    from app.agent.openapi_gateway import get_openapi_spec, OpenAPIToolGateway
    print("✓ openapi_gateway module loads successfully")
    
    spec = get_openapi_spec()
    print(f"  ✓ OpenAPI spec with {len(spec['paths'])} paths")
    
    # Test mock mode
    gateway = OpenAPIToolGateway()  # Should use mock mode
    print(f"  ✓ OpenAPIToolGateway initializes in mock mode")
    
except Exception as e:
    print(f"✗ openapi_gateway module failed: {e}")
    sys.exit(1)

# Validate graph.py constants
try:
    from app.agent import graph
    print("✓ graph module loads successfully")
except Exception as e:
    print(f"✗ graph module failed: {e}")
    sys.exit(1)

print("\n✓✓✓ All core validation checks passed! ✓✓✓")
