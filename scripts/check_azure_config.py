#!/usr/bin/env python3
"""Script pour vérifier la configuration Azure AD SSO."""

import os
import sys
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def check_env_vars():
    """Vérifier que toutes les variables d'environnement nécessaires sont définies."""
    print("=== Vérification des variables d'environnement ===")
    
    required_vars = {
        "AZURE_AD_TENANT_ID": os.getenv("AZURE_AD_TENANT_ID"),
        "AZURE_AD_CLIENT_ID": os.getenv("AZURE_AD_CLIENT_ID"),
        "AZURE_AD_CLIENT_SECRET": os.getenv("AZURE_AD_CLIENT_SECRET"),
        "AZURE_AD_REDIRECT_URI": os.getenv("AZURE_AD_REDIRECT_URI", "http://localhost:3200/auth/callback"),
    }
    
    all_present = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Masquer le secret
            if "SECRET" in var_name:
                display_value = f"{var_value[:8]}...{var_value[-4:]}" if len(var_value) > 12 else "***"
            else:
                display_value = var_value
            print(f"✓ {var_name}: {display_value}")
        else:
            print(f"✗ {var_name}: NON DÉFINIE")
            all_present = False
    
    return all_present

def check_azure_endpoints():
    """Vérifier que les endpoints Azure AD sont accessibles."""
    print("\n=== Vérification des endpoints Azure AD ===")
    
    tenant_id = os.getenv("AZURE_AD_TENANT_ID")
    if not tenant_id:
        print("✗ Impossible de vérifier les endpoints sans AZURE_AD_TENANT_ID")
        return False
    
    # Endpoints à vérifier
    endpoints = {
        "Authority": f"https://login.microsoftonline.com/{tenant_id}",
        "OpenID Config": f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration",
    }
    
    all_accessible = True
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {name}: Accessible")
            else:
                print(f"✗ {name}: Status {response.status_code}")
                all_accessible = False
        except Exception as e:
            print(f"✗ {name}: Erreur - {str(e)}")
            all_accessible = False
    
    return all_accessible

def check_redirect_uri():
    """Vérifier la configuration de l'URI de redirection."""
    print("\n=== Configuration de l'URI de redirection ===")
    
    redirect_uri = os.getenv("AZURE_AD_REDIRECT_URI", "http://localhost:3200/auth/callback")
    print(f"URI configurée: {redirect_uri}")
    
    print("\n⚠️  IMPORTANT: Assurez-vous que cette URI est ajoutée dans Azure Portal:")
    print("1. Allez sur https://portal.azure.com")
    print("2. Azure Active Directory > App registrations")
    print("3. Sélectionnez votre application")
    print("4. Authentication > Platform configurations > Web")
    print(f"5. Vérifiez que '{redirect_uri}' est dans la liste des Redirect URIs")
    
    return True

def check_api_status():
    """Vérifier que l'API backend répond correctement."""
    print("\n=== Vérification de l'API backend ===")
    
    api_url = "http://localhost:8000/api/v1/auth/sso/status"
    
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API SSO Status:")
            print(f"  - Enabled: {data.get('enabled', False)}")
            print(f"  - Configured: {data.get('configured', False)}")
            print(f"  - Mandatory: {data.get('mandatory', False)}")
            print(f"  - Provider: {data.get('provider', 'N/A')}")
            return data.get('configured', False)
        else:
            print(f"✗ API Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Erreur de connexion à l'API: {str(e)}")
        print("  Assurez-vous que le backend est démarré (docker compose up)")
        return False

def generate_test_url():
    """Générer une URL de test pour l'authentification."""
    print("\n=== URL de test ===")
    
    client_id = os.getenv("AZURE_AD_CLIENT_ID")
    tenant_id = os.getenv("AZURE_AD_TENANT_ID")
    redirect_uri = os.getenv("AZURE_AD_REDIRECT_URI", "http://localhost:3200/auth/callback")
    
    if client_id and tenant_id:
        auth_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?"
            f"client_id={client_id}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&scope=openid%20profile%20email%20User.Read"
            f"&response_mode=query"
        )
        
        print("URL d'authentification Azure AD (pour test manuel):")
        print(auth_url)
        print("\nVous pouvez copier cette URL dans votre navigateur pour tester l'authentification.")
        return True
    else:
        print("✗ Impossible de générer l'URL sans CLIENT_ID et TENANT_ID")
        return False

def main():
    """Fonction principale."""
    print("🔍 Vérification de la configuration Azure AD SSO")
    print("=" * 50)
    
    # Vérifications
    env_ok = check_env_vars()
    azure_ok = check_azure_endpoints()
    redirect_ok = check_redirect_uri()
    api_ok = check_api_status()
    url_ok = generate_test_url()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé de la vérification:")
    
    checks = {
        "Variables d'environnement": env_ok,
        "Endpoints Azure AD": azure_ok,
        "URI de redirection": redirect_ok,
        "API Backend": api_ok,
        "URL de test": url_ok,
    }
    
    all_ok = all(checks.values())
    
    for check_name, check_result in checks.items():
        status = "✓" if check_result else "✗"
        print(f"{status} {check_name}")
    
    if all_ok:
        print("\n✅ Configuration SSO correcte!")
        print("\n🚀 Prochaines étapes:")
        print("1. Accédez à http://localhost:3200")
        print("2. Cliquez sur 'Se connecter avec Microsoft'")
        print("3. Connectez-vous avec un compte @nda-partners.com")
    else:
        print("\n❌ Des problèmes ont été détectés.")
        print("Corrigez les points marqués d'un ✗ ci-dessus.")
        
        if not env_ok:
            print("\n💡 Conseil: Vérifiez votre fichier .env")
        if not azure_ok:
            print("\n💡 Conseil: Vérifiez votre Tenant ID")
        if not api_ok:
            print("\n💡 Conseil: Démarrez le backend avec 'docker compose up'")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())