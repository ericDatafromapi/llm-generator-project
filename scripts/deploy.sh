#!/bin/bash

# LLMReady Production Deployment Script
# This script triggers the GitHub Actions deployment workflow from VSCode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="${GITHUB_REPO_OWNER:-}"
REPO_NAME="${GITHUB_REPO_NAME:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 LLMReady Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Get repository information from git remote
if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
    REMOTE_URL=$(git config --get remote.origin.url)
    if [[ $REMOTE_URL == *"github"* ]]; then
        # Extract owner and repo from GitHub URL
        if [[ $REMOTE_URL == git@* ]]; then
            # SSH format: git@github.com:owner/repo.git or git@custom-alias:owner/repo.git
            REPO_PATH=$(echo $REMOTE_URL | sed 's/git@[^:]*://' | sed 's/.git$//')
        else
            # HTTPS format: https://github.com/owner/repo.git
            REPO_PATH=$(echo $REMOTE_URL | sed 's#https://github.com/##' | sed 's/.git$//')
        fi
        REPO_OWNER=$(echo $REPO_PATH | cut -d'/' -f1)
        REPO_NAME=$(echo $REPO_PATH | cut -d'/' -f2)
    fi
fi

if [ -z "$REPO_OWNER" ] || [ -z "$REPO_NAME" ]; then
    echo -e "${RED}❌ Error: Could not determine repository owner and name${NC}"
    echo -e "${YELLOW}Please set GITHUB_REPO_OWNER and GITHUB_REPO_NAME environment variables${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not found in environment${NC}"
    echo -e "${YELLOW}Please enter your GitHub Personal Access Token:${NC}"
    read -s GITHUB_TOKEN
    echo ""
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Error: GitHub token is required${NC}"
    echo -e "${YELLOW}Create a token at: https://github.com/settings/tokens${NC}"
    echo -e "${YELLOW}Required scopes: repo, workflow${NC}"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${GREEN}🌿 Current branch: ${CURRENT_BRANCH}${NC}\n"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    echo -e "${YELLOW}Do you want to continue? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 1
    fi
fi

# Confirm deployment
echo -e "${YELLOW}⚠️  You are about to deploy to PRODUCTION${NC}"
echo -e "${YELLOW}Branch: ${CURRENT_BRANCH}${NC}"
echo -e "${YELLOW}Commit: $(git rev-parse --short HEAD) - $(git log -1 --pretty=%B | head -n 1)${NC}\n"
echo -e "${YELLOW}Type 'deploy' to confirm:${NC}"
read -r confirmation

if [ "$confirmation" != "deploy" ]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

echo -e "\n${BLUE}🚀 Triggering deployment workflow...${NC}\n"

# Trigger the workflow using GitHub API
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/deploy-production.yml/dispatches" \
    -d "{\"ref\":\"${CURRENT_BRANCH}\",\"inputs\":{\"confirm\":\"deploy\"}}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 204 ]; then
    echo -e "${GREEN}✅ Deployment workflow triggered successfully!${NC}\n"
    echo -e "${BLUE}📊 View workflow run at:${NC}"
    echo -e "${BLUE}https://github.com/${REPO_OWNER}/${REPO_NAME}/actions${NC}\n"
    
    # Wait a moment and try to get the workflow run URL
    sleep 3
    RUNS=$(curl -s -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?event=workflow_dispatch&per_page=1")
    
    RUN_URL=$(echo "$RUNS" | grep -o '"html_url": "[^"]*' | head -1 | cut -d'"' -f4)
    if [ ! -z "$RUN_URL" ]; then
        echo -e "${GREEN}🔗 Direct link: ${RUN_URL}${NC}\n"
    fi
    
    echo -e "${BLUE}💡 You will receive an email notification when deployment completes${NC}"
else
    echo -e "${RED}❌ Failed to trigger deployment${NC}"
    echo -e "${RED}HTTP Status: ${HTTP_CODE}${NC}"
    echo -e "${RED}Response: ${BODY}${NC}\n"
    
    if [ "$HTTP_CODE" -eq 401 ]; then
        echo -e "${YELLOW}💡 Your GitHub token may be invalid or expired${NC}"
        echo -e "${YELLOW}Create a new token at: https://github.com/settings/tokens${NC}"
    elif [ "$HTTP_CODE" -eq 404 ]; then
        echo -e "${YELLOW}💡 Workflow file not found or you don't have access${NC}"
        echo -e "${YELLOW}Make sure the workflow file exists and you have push access${NC}"
    fi
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✨ Deployment initiated successfully!${NC}"
echo -e "${BLUE}========================================${NC}"