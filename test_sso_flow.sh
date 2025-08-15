#!/bin/bash

echo "🧪 Test du flux SSO Azure AD"
echo "============================"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier que le backend est accessible
echo -e "\n${YELLOW}1. Vérification du backend...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/sso/status)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓ Backend accessible${NC}"
    status=$(curl -s http://localhost:8000/api/v1/auth/sso/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'  - SSO Enabled: {data[\"enabled\"]}\\n  - Configured: {data[\"configured\"]}\\n  - Mandatory: {data[\"mandatory\"]}')")
    echo "$status"
else
    echo -e "${RED}✗ Backend non accessible (HTTP $response)${NC}"
    exit 1
fi

# 2. Vérifier la base de données
echo -e "\n${YELLOW}2. État de la base de données...${NC}"
token_count=$(docker compose exec -T postgres psql -U plancharge -d plancharge -t -c "SELECT COUNT(*) FROM refresh_tokens;" | tr -d ' ')
user_count=$(docker compose exec -T postgres psql -U plancharge -d plancharge -t -c "SELECT COUNT(*) FROM users WHERE azure_id IS NOT NULL;" | tr -d ' ')
echo -e "  - Refresh tokens: $token_count"
echo -e "  - Utilisateurs SSO: $user_count"

# 3. Générer l'URL de connexion SSO
echo -e "\n${YELLOW}3. URL de connexion SSO...${NC}"
echo -e "${GREEN}Pour tester la connexion :${NC}"
echo ""
echo "1. Ouvrez votre navigateur à : http://localhost:3200"
echo "2. Cliquez sur 'Se connecter avec Microsoft'"
echo "3. Connectez-vous avec un compte @nda-partners.com"
echo ""
echo "OU utilisez cette URL directe :"
echo ""
echo "https://login.microsoftonline.com/1e1ef656-4a7f-4ea3-b5b8-2713d2e6f74d/oauth2/v2.0/authorize?client_id=5f6d8aed-0572-407e-8981-e379330c5c53&response_type=code&redirect_uri=http://localhost:3200/auth/callback&scope=openid%20profile%20email%20User.Read&response_mode=query"

# 4. Surveiller les logs
echo -e "\n${YELLOW}4. Surveillance des logs...${NC}"
echo "Pour voir les logs en temps réel pendant le test :"
echo "  docker compose logs -f backend"

echo -e "\n${GREEN}✅ Système prêt pour le test SSO !${NC}"