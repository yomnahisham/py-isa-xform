 #!/bin/bash

# py-isa-xform Release Script
# Usage: ./release.sh <version>
# Example: ./release.sh 1.0.0

set -e  # Exit on any error

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.0"
    exit 1
fi

echo "🚀 Creating release v$VERSION..."

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Error: You must be on the main branch to create a release"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean"
    echo "Please commit or stash your changes first"
    git status --short
    exit 1
fi

# Update version in __init__.py
echo "📝 Updating version to $VERSION..."
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/isa_xform/__init__.py
rm src/isa_xform/__init__.py.bak

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Build package
echo "📦 Building package..."
python -m build

# Test installation
echo "🔧 Testing installation..."
pip install dist/py_isa_xform-$VERSION-py3-none-any.whl --force-reinstall

# Commit changes
echo "💾 Committing changes..."
git add src/isa_xform/__init__.py
git commit -m "Release v$VERSION"

# Push to main
echo "📤 Pushing to main..."
git push origin main

# Create and push tag
echo "🏷️ Creating tag v$VERSION..."
git tag v$VERSION
git push origin v$VERSION

echo ""
echo "✅ Release v$VERSION created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. GitHub Actions will automatically build and create the release"
echo "2. Check: https://github.com/yomnahisham/py-isa-xform/releases"
echo "3. Verify the release assets are uploaded"
echo ""
echo "📥 Users can now install with:"
echo "   pip install git+https://github.com/yomnahisham/py-isa-xform.git@v$VERSION"
echo "   or"
echo "   pip install https://github.com/yomnahisham/py-isa-xform/releases/download/v$VERSION/py_isa_xform-$VERSION-py3-none-any.whl"