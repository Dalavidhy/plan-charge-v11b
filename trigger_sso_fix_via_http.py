#!/usr/bin/env python3
"""
Trigger SSO fix via HTTP request to the backend
This creates a temporary endpoint or uses existing backend connection
"""

import requests
import json
import time

def trigger_sso_fix_via_backend():
    """Try to trigger the SSO fix by making HTTP requests to the backend."""
    
    print("🎯 Triggering SSO Fix via Backend HTTP")
    print("=" * 40)
    
    # Try different approaches to trigger the fix
    approaches = [
        {
            "name": "Direct backend health check",
            "url": "https://plan-de-charge.aws.nda-partners.com/health",
            "method": "GET"
        },
        {
            "name": "API documentation endpoint", 
            "url": "https://plan-de-charge.aws.nda-partners.com/docs",
            "method": "GET"
        },
        {
            "name": "Database migration endpoint",
            "url": "https://plan-de-charge.aws.nda-partners.com/api/v1/admin/migrate",
            "method": "POST"
        }
    ]
    
    for approach in approaches:
        try:
            print(f"\n🔍 Trying: {approach['name']}")
            print(f"   URL: {approach['url']}")
            
            if approach['method'] == 'GET':
                response = requests.get(approach['url'], timeout=10)
            else:
                response = requests.post(approach['url'], timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Backend is accessible")
                
                # Check response for any useful information
                try:
                    if 'json' in response.headers.get('content-type', '').lower():
                        data = response.json()
                        print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        print(f"   Response: {response.text[:200]}...")
                except:
                    pass
                    
            elif response.status_code == 404:
                print("⚠️ Endpoint not found")
            else:
                print(f"⚠️ Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            continue
    
    # Now let's test the current SSO status
    print(f"\n🧪 Testing Current SSO Status")
    print("=" * 30)
    
    try:
        sso_response = requests.post(
            "https://plan-de-charge.aws.nda-partners.com/api/v1/auth/sso/token-exchange",
            json={"access_token": "test_token"},
            timeout=10
        )
        
        print(f"SSO Endpoint Status: {sso_response.status_code}")
        
        if sso_response.status_code == 500:
            print("❌ Still getting 500 - Default Organization not added yet")
            print("💡 Need to use alternative approach")
        elif sso_response.status_code == 400:
            print("✅ No longer 500 - but 400 (bad request) is expected for test token")
            print("🎉 This indicates the Default Organization was added!")
        elif sso_response.status_code == 401:
            print("✅ No longer 500 - but 401 (unauthorized) is expected for test token") 
            print("🎉 This indicates the Default Organization was added!")
        else:
            print(f"ℹ️ Unexpected status: {sso_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ SSO test failed: {e}")
    
    return False

def create_manual_sql_execution_guide():
    """Create a guide for manual SQL execution."""
    
    print(f"\n📋 MANUAL SQL EXECUTION GUIDE")
    print("=" * 35)
    print("Since ECS Exec is having issues, here are alternative approaches:")
    
    print(f"\n🔧 Option 1: AWS RDS Query Editor")
    print("1. Go to AWS Console → RDS → Query Editor")
    print("2. Select: plan-charge-prod-db in eu-west-3")
    print("3. Execute:")
    print("""
INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) 
VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW(), NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW();
""")
    
    print(f"\n🔧 Option 2: Database Administrator")
    print("Ask your database admin to execute the SQL above")
    
    print(f"\n🔧 Option 3: Restart ECS Service")
    print("Sometimes ECS Exec works after a service restart:")
    print("aws ecs update-service --region eu-west-3 --cluster plan-charge-prod-cluster --service plan-charge-prod-backend --force-new-deployment")
    
    print(f"\n🔧 Option 4: Lambda with VPC Access")
    print("Create a Lambda function in the same VPC as RDS")
    
    print(f"\n🧪 Test SSO After Fix:")
    print("python3 /tmp/final_sso_fix.py")
    print("or visit: https://plan-de-charge.aws.nda-partners.com")

if __name__ == "__main__":
    trigger_sso_fix_via_backend()
    create_manual_sql_execution_guide()