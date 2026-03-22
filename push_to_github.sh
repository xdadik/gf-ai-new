#!/bin/bash
# GitHub Push Script for Nova AI
# ================================
# ⚠️  PRIVACY WARNING: You previously asked to keep this code PRIVATE
#     This script will push to GitHub. Make sure:
#     1. Your .env file is in .gitignore (it is)
#     2. Your repo is PRIVATE if you want privacy
#     3. Review the .gitignore file before pushing

echo "🚀 Nova AI GitHub Push Script"
echo "==============================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    
    # Set up remote (user needs to provide their repo URL)
    echo ""
    echo "⚠️  You need to add your GitHub remote:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo ""
    exit 1
fi

# Check remote
echo "📡 Checking remote..."
git remote -v

# Check .gitignore
echo ""
echo "🔒 Checking .gitignore protections..."
if grep -q "personalities.py" .gitignore; then
    echo "   ✅ personalities.py is protected"
else
    echo "   ⚠️  WARNING: personalities.py is NOT in .gitignore!"
fi

if grep -q ".env" .gitignore; then
    echo "   ✅ .env is protected"
else
    echo "   ⚠️  WARNING: .env is NOT in .gitignore!"
fi

# Check for sensitive files before committing
echo ""
echo "🔍 Scanning for sensitive files..."
SENSITIVE_FILES=$(git ls-files | grep -E "(.env|secrets|token|key|personalities\.py)" || true)
if [ -n "$SENSITIVE_FILES" ]; then
    echo "   ⚠️  WARNING: These sensitive files might be committed:"
    echo "$SENSITIVE_FILES"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Push cancelled."
        exit 1
    fi
else
    echo "   ✅ No obvious sensitive files found in tracking"
fi

# Add files
echo ""
echo "📁 Adding files to git..."
git add .

# Check status
echo ""
echo "📊 Git status:"
git status -s

# Commit
echo ""
read -p "Enter commit message: " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update Nova AI - $(date +%Y-%m-%d)"
fi

git commit -m "$commit_msg"

# Push
echo ""
echo "🚀 Pushing to GitHub..."
read -p "Push to origin main? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    echo ""
    echo "✅ Push complete!"
else
    echo "❌ Push cancelled."
    echo "   You can push manually later with: git push origin main"
fi

echo ""
echo "📝 Next steps:"
echo "   - Check your repo on GitHub"
echo "   - Verify no sensitive files were pushed"
echo "   - If you see secrets, REMOVE THEM IMMEDIATELY"
