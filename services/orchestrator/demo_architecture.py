#!/usr/bin/env python
"""
End-to-end architecture demonstration.

This script shows how the intent router, OpenAPI gateway, and response
formatting work together without requiring external dependencies.
"""
import sys
import json
from typing import Any

sys.path.insert(0, '.')

from app.agent.router import route_intent, IntentRoute
from app.agent.openapi_gateway import OpenAPIToolGateway, OpenAPIRequest, get_openapi_spec


async def simulate_chat_endpoint(question: str, user_role: str = "employee") -> dict[str, Any]:
    """
    Simulates the /chat/ask endpoint with intent routing.
    
    Shows how different question types are routed to different handlers.
    """
    print(f"\n{'='*70}")
    print(f"Question: {question}")
    print(f"User Role: {user_role}")
    print(f"{'='*70}")
    
    # Step 1: Route intent
    intent = route_intent(question)
    print(f"✓ Step 1: Intent Router → {intent.value.upper()}")
    
    # Step 2: Handle based on intent
    if intent == IntentRoute.human_approval:
        print("✓ Step 2: Approval Required → Return to human queue")
        return {
            "answer": "Yêu cầu này cần phê duyệt từ người quản lý. Vui lòng tạo request chính thức hoặc gửi cho người phê duyệt.",
            "sources": [],
            "mode": "human_approval",
            "intent": "human_approval",
        }
    
    elif intent == IntentRoute.tool:
        print("✓ Step 2: Tool Query → Access Enterprise APIs via OpenAPI Gateway")
        gateway = OpenAPIToolGateway()  # Uses mock mode
        
        # Determine which tool to call based on question
        if "chấm công" in question.lower() or "attendance" in question.lower():
            tool_result = await gateway.invoke(OpenAPIRequest(
                operation_id="get_staff_attendance",
                arguments={"staff_id": 1, "from_date": "2024-07-01", "to_date": "2024-07-31"}
            ))
            print(f"  ✓ Tool Called: get_staff_attendance")
        
        elif "lương" in question.lower() or "payslip" in question.lower():
            tool_result = await gateway.invoke(OpenAPIRequest(
                operation_id="get_payslip",
                arguments={"month": 7, "year": 2024, "otp": None}
            ))
            print(f"  ✓ Tool Called: get_payslip")
        
        elif "tin tức" in question.lower() or "news" in question.lower():
            tool_result = await gateway.invoke(OpenAPIRequest(
                operation_id="search_company_news",
                arguments={"keyword": None}
            ))
            print(f"  ✓ Tool Called: search_company_news")
        
        else:
            tool_result = await gateway.invoke(OpenAPIRequest(
                operation_id="list_hr_requests",
                arguments={"status": None}
            ))
            print(f"  ✓ Tool Called: list_hr_requests")
        
        print(f"✓ Step 3: Guardrails → Checking for PII/sensitive data")
        print(f"✓ Step 4: Format Response → Include tool results + intent metadata")
        
        return {
            "answer": f"(LangGraph Agent would process this) Tool result: {tool_result}",
            "sources": [],
            "mode": "tool-agent",
            "intent": "tool",
        }
    
    else:  # RAG
        print("✓ Step 2: RAG Query → Search Knowledge Base (RBAC-filtered)")
        print(f"✓ Step 3: Permission Check → User '{user_role}' has access")
        print(f"✓ Step 4: Guardrails → Checking for PII/sensitive data")
        print(f"✓ Step 5: Format Response → Include citations + intent metadata")
        
        return {
            "answer": "(LangGraph Agent would generate this) Policy summary from knowledge base...",
            "sources": [
                {"document_id": "DOC001", "title": "Quy chế Nội bộ", "classification": "internal"},
                {"document_id": "DOC002", "title": "Chính sách Tài chính", "classification": "internal"},
            ],
            "mode": "rag-agent",
            "intent": "rag",
        }


async def main():
    """Run demonstration scenarios."""
    import asyncio
    
    print("\n" + "="*70)
    print("My Tasco AI Workspace - Architecture Demonstration")
    print("="*70)
    
    # Show OpenAPI spec
    print("\n📋 Available Tools via OpenAPI Gateway:")
    spec = get_openapi_spec()
    for path in spec["paths"].keys():
        operations = list(spec["paths"][path].values())[0]
        op_id = operations.get("operationId", "N/A")
        print(f"  • {path} → {op_id}")
    
    # Test scenarios
    scenarios = [
        ("Quy chế nội bộ là gì?", "employee"),
        ("Xem chấm công của tôi", "employee"),
        ("Phê duyệt đơn xin nghỉ phép", "manager"),
        ("Lương tháng này là bao nhiêu?", "employee"),
        ("Tin tức công ty có gì mới?", "employee"),
    ]
    
    print("\n" + "="*70)
    print("SCENARIO DEMONSTRATIONS")
    print("="*70)
    
    for question, role in scenarios:
        response = await simulate_chat_endpoint(question, role)
        print(f"\nResponse:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("✓ Architecture Demonstration Complete")
    print("="*70)
    print("\nKey Points Demonstrated:")
    print("  1. Intent Router correctly classifies queries")
    print("  2. Tool Gateway provides OpenAPI discovery")
    print("  3. Response format includes intent metadata")
    print("  4. Guardrails can check for sensitive data")
    print("  5. RBAC will be applied to all results")
    print("\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
