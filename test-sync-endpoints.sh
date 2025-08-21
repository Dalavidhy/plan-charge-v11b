#!/bin/bash

# Test script for sync endpoints
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Test des endpoints de synchronisation${NC}"
echo "======================================"

# Backend health check
echo -e "\n${BLUE}1. Test de santé du backend${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
  echo -e "${GREEN}✅ Backend accessible sur http://localhost:8000${NC}"
  curl -s http://localhost:8000/health | jq .
else
  echo -e "${RED}❌ Backend non accessible${NC}"
  exit 1
fi

# Frontend check
echo -e "\n${BLUE}2. Test du frontend${NC}"
if curl -s http://localhost:3200 | grep -q "<!DOCTYPE html"; then
  echo -e "${GREEN}✅ Frontend accessible sur http://localhost:3200${NC}"
else
  echo -e "${RED}❌ Frontend non accessible${NC}"
  exit 1
fi

# Configuration check
echo -e "\n${BLUE}3. Vérification des configurations${NC}"

# Check backend .env
if [ -f "./backend/.env" ]; then
  echo -e "${GREEN}✅ Backend .env existe${NC}"
  echo "Payfit API URL: $(grep PAYFIT_API_URL ./backend/.env | cut -d'=' -f2)"
  echo "Gryzzly API URL: $(grep GRYZZLY_API_URL ./backend/.env | cut -d'=' -f2)"
  echo "Gryzzly Mock Mode: $(grep GRYZZLY_USE_MOCK ./backend/.env | cut -d'=' -f2)"
else
  echo -e "${RED}❌ Backend .env non trouvé${NC}"
fi

# Check frontend .env
if [ -f "./frontend/.env" ]; then
  echo -e "${GREEN}✅ Frontend .env existe${NC}"
  echo "Frontend API URL: $(grep VITE_API_URL ./frontend/.env | cut -d'=' -f2)"
  echo "Frontend Gryzzly Mock: $(grep VITE_GRYZZLY_USE_MOCK ./frontend/.env | cut -d'=' -f2)"
else
  echo -e "${RED}❌ Frontend .env non trouvé${NC}"
fi

# API endpoints test (without auth - should return 401/403)
echo -e "\n${BLUE}4. Test des endpoints API (sans auth)${NC}"

echo -n "Payfit status: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/payfit/status)
if [ "$STATUS" = "403" ] || [ "$STATUS" = "401" ]; then
  echo -e "${GREEN}✅ Endpoint protégé (HTTP $STATUS)${NC}"
else
  echo -e "${YELLOW}⚠️  HTTP $STATUS (attendu 401/403)${NC}"
fi

echo -n "Gryzzly status: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/gryzzly/status)
if [ "$STATUS" = "403" ] || [ "$STATUS" = "401" ]; then
  echo -e "${GREEN}✅ Endpoint protégé (HTTP $STATUS)${NC}"
else
  echo -e "${YELLOW}⚠️  HTTP $STATUS (attendu 401/403)${NC}"
fi

# Docker containers check
echo -e "\n${BLUE}5. Vérification des conteneurs Docker${NC}"
if docker compose ps | grep -q "Up.*healthy"; then
  echo -e "${GREEN}✅ Conteneurs Docker opérationnels${NC}"
  docker compose ps --format table
else
  echo -e "${YELLOW}⚠️  Certains conteneurs pourraient avoir des problèmes${NC}"
  docker compose ps --format table
fi

echo -e "\n${BLUE}📋 Instructions pour tester l'interface${NC}"
echo "======================================"
echo -e "1. Ouvrez ${YELLOW}http://localhost:3200/sync${NC} dans votre navigateur"
echo -e "2. Connectez-vous si nécessaire"
echo -e "3. Allez dans l'onglet ${YELLOW}Diagnostic${NC}"
echo -e "4. Cliquez sur ${YELLOW}'Lancer le diagnostic'${NC}"
echo -e "5. Vérifiez que tous les tests passent"
echo -e "6. Testez les onglets ${YELLOW}Payfit${NC} et ${YELLOW}Gryzzly${NC}"
echo -e "7. Cliquez sur ${YELLOW}'Tester la connexion'${NC} dans chaque onglet"

echo -e "\n${GREEN}🎉 Test des endpoints terminé!${NC}"
