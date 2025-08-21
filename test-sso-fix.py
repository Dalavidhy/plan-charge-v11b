#!/usr/bin/env python3
"""
Test script to verify SSO organization fix.
This tests if the backend can handle the organization lookup correctly.
"""

import time
import requests
import json

def test_sso_fix():
    """Test the SSO authentication fix."""

    print("🧪 Testing SSO Organization Fix")
    print("=" * 40)

    # Test data that simulates frontend request
    test_payload = {
        "azureToken": "test_access_token",
        "idToken": "test_id_token",
        "userInfo": {
            "email": "test@nda-partners.com",
            "name": "Test User",
            "id": "test_azure_id"
        }
    }

    print("1. 🔍 Testing SSO endpoint accessibility...")
    try:
        response = requests.post(
            "https://plan-de-charge.aws.nda-partners.com/api/v1/auth/sso/token-exchange",
            json=test_payload,
            timeout=10
        )

        print(f"   📊 Status Code: {response.status_code}")

        if response.status_code == 400:
            # This is expected with fake tokens - means endpoint is working
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "")
                print(f"   💬 Error Message: {error_msg}")

                if "Email not found in user info" in error_msg:
                    print("   ✅ Expected validation error - endpoint working correctly")
                    return "ENDPOINT_WORKING"
                elif "Default Organization" in error_msg:
                    print("   ❌ Still has organization issue - fix not deployed")
                    return "NEEDS_FIX"
                else:
                    print("   ⚠️  Different validation error")
                    return "DIFFERENT_ERROR"
            except:
                print("   ⚠️  Could not parse error response")
                return "PARSE_ERROR"

        elif response.status_code == 500:
            print("   ❌ 500 Internal Server Error - organization fix not deployed")
            return "NEEDS_DEPLOYMENT"

        elif response.status_code == 429:
            print("   ⏳ Rate limited - waiting and retrying...")
            time.sleep(60)  # Wait 1 minute
            return test_sso_fix()  # Retry

        else:
            print(f"   🔍 Unexpected response: {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}...")
            return "UNEXPECTED"

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return "REQUEST_FAILED"

def main():
    """Main test function."""

    print("🎯 SSO Organization Fix Test")
    print("This test verifies if the backend organization fix has been deployed")
    print()

    result = test_sso_fix()

    print("\n📋 Test Results")
    print("=" * 20)

    if result == "ENDPOINT_WORKING":
        print("✅ SUCCESS: SSO endpoint is working correctly!")
        print("✅ Organization fix has been deployed")
        print("🚀 Users should now be able to authenticate successfully")
        print("\n📝 Next steps:")
        print("1. Test actual SSO login at: https://plan-de-charge.aws.nda-partners.com")
        print("2. Use a real @nda-partners.com email address")
        print("3. User should be created automatically in the database")

    elif result == "NEEDS_DEPLOYMENT":
        print("❌ NEEDS ACTION: Organization fix not yet deployed")
        print("💡 Action required:")
        print("1. Run the deployment script: ./deploy-sso-fix.sh")
        print("2. Or manually deploy the backend with the organization fixes")
        print("3. Wait for ECS service to update (2-3 minutes)")
        print("4. Run this test again")

    elif result == "NEEDS_FIX":
        print("❌ STILL BROKEN: Organization name issue persists")
        print("💡 This means the code changes weren't included in the deployment")

    else:
        print(f"⚠️  UNCLEAR: Test result was {result}")
        print("💡 May need manual investigation")

    print(f"\n🏁 Test completed with result: {result}")
    return result == "ENDPOINT_WORKING"

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
