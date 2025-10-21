#!/bin/bash
# scripts/update_changelog.sh
# Purpose: Generate and update CHANGELOG.md from git commit history using Conventional Commits

set -e

# Configuration
CHANGELOG_FILE="CHANGELOG.md"
VERSION_FILE="VERSION"
REPO_URL="https://github.com/MitPete/Micro-Consent-Pipeline"

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Generate and update CHANGELOG.md from git commit history"
    echo ""
    echo "OPTIONS:"
    echo "  -t, --tag VERSION       Generate changelog for specific version tag"
    echo "  -r, --release           Generate changelog for new release (auto-bump version)"
    echo "  -p, --preview           Preview changelog without writing to file"
    echo "  -f, --full              Generate full changelog from all commits"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                      # Update changelog with unreleased changes"
    echo "  $0 -r                   # Generate changelog for new release"
    echo "  $0 -t v1.0.1           # Generate changelog for specific version"
    echo "  $0 -p                   # Preview changes without writing"
}

# Parse command line arguments
RELEASE_MODE=false
PREVIEW_MODE=false
FULL_MODE=false
VERSION_TAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            VERSION_TAG="$2"
            shift 2
            ;;
        -r|--release)
            RELEASE_MODE=true
            shift
            ;;
        -p|--preview)
            PREVIEW_MODE=true
            shift
            ;;
        -f|--full)
            FULL_MODE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

echo "========================================="
echo "Micro-Consent Pipeline Changelog Generator"
echo "========================================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Get current version
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE")
    echo "Current version: $CURRENT_VERSION"
else
    echo "Warning: VERSION file not found, using 0.0.0"
    CURRENT_VERSION="0.0.0"
fi

# Function to determine next version based on commit types
determine_next_version() {
    local current_version="$1"
    local has_breaking=false
    local has_feat=false
    local has_fix=false

    # Parse current version
    local major minor patch
    IFS='.' read -r major minor patch <<< "$current_version"

    # Check recent commits for conventional commit types
    local commits
    if [ -n "$VERSION_TAG" ]; then
        commits=$(git log --oneline --pretty=format:"%s" "$VERSION_TAG..HEAD")
    else
        # Get commits since last tag, or all commits if no tags
        local last_tag
        last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        if [ -n "$last_tag" ]; then
            commits=$(git log --oneline --pretty=format:"%s" "$last_tag..HEAD")
        else
            commits=$(git log --oneline --pretty=format:"%s")
        fi
    fi

    # Analyze commit types
    while IFS= read -r commit; do
        if echo "$commit" | grep -q "BREAKING CHANGE\|^[a-zA-Z]*!:"; then
            has_breaking=true
        elif echo "$commit" | grep -q "^feat:"; then
            has_feat=true
        elif echo "$commit" | grep -q "^fix:"; then
            has_fix=true
        fi
    done <<< "$commits"

    # Determine version bump
    if [ "$has_breaking" = true ]; then
        # Major version bump
        major=$((major + 1))
        minor=0
        patch=0
    elif [ "$has_feat" = true ]; then
        # Minor version bump
        minor=$((minor + 1))
        patch=0
    elif [ "$has_fix" = true ]; then
        # Patch version bump
        patch=$((patch + 1))
    else
        # No version bump needed
        echo "$current_version"
        return
    fi

    echo "$major.$minor.$patch"
}

# Determine target version
if [ "$RELEASE_MODE" = true ]; then
    if [ -z "$VERSION_TAG" ]; then
        NEW_VERSION=$(determine_next_version "$CURRENT_VERSION")
        VERSION_TAG="v$NEW_VERSION"
        echo "Auto-determined next version: $NEW_VERSION"
    else
        NEW_VERSION="${VERSION_TAG#v}"
    fi

    # Update VERSION file
    echo "$NEW_VERSION" > "$VERSION_FILE"
    echo "Updated VERSION file to $NEW_VERSION"
elif [ -n "$VERSION_TAG" ]; then
    NEW_VERSION="${VERSION_TAG#v}"
    echo "Generating changelog for version: $VERSION_TAG"
else
    NEW_VERSION="Unreleased"
    echo "Generating changelog for unreleased changes"
fi

# Create temporary configuration for git-changelog
TEMP_CONFIG=$(mktemp)
cat > "$TEMP_CONFIG" << EOF
[tool.git-changelog]
convention = "conventional"
template = "keepachangelog"
parse_refs = true
parse_trailers = true
sections = [
    {name = "Features", types = ["feat"]},
    {name = "Bug Fixes", types = ["fix"]},
    {name = "Documentation", types = ["docs"]},
    {name = "Performance", types = ["perf"]},
    {name = "Refactoring", types = ["refactor"]},
    {name = "Testing", types = ["test"]},
    {name = "Build System", types = ["build", "ci", "chore"]},
    {name = "Other", types = ["style", "revert", "other"]}
]
EOF

# Generate changelog content
echo ""
echo "Generating changelog..."

if [ "$FULL_MODE" = true ]; then
    # Generate full changelog from all history
    CHANGELOG_CONTENT=$(git-changelog --config-file "$TEMP_CONFIG" --output json | \
        python3 -c "
import json
import sys
from datetime import datetime

data = json.load(sys.stdin)
print('# Changelog')
print('')
print('All notable changes to this project will be documented in this file.')
print('')
print('The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),')
print('and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).')
print('')

for version in data.get('versions', []):
    version_name = version.get('tag', 'Unreleased')
    version_date = version.get('date', datetime.now().strftime('%Y-%m-%d'))
    print(f'## [{version_name}] - {version_date}')
    print('')

    for section in version.get('sections', []):
        if section.get('commits'):
            print(f'### {section[\"title\"]}')
            print('')
            for commit in section['commits']:
                subject = commit.get('subject', '')
                if subject:
                    print(f'- {subject}')
            print('')
")
else
    # Generate changelog for recent changes
    if [ -n "$VERSION_TAG" ] && [ "$VERSION_TAG" != "Unreleased" ]; then
        # Get last tag for comparison
        LAST_TAG=$(git describe --tags --abbrev=0 "$VERSION_TAG^" 2>/dev/null || echo "")
        if [ -n "$LAST_TAG" ]; then
            RANGE="$LAST_TAG..$VERSION_TAG"
        else
            RANGE="$VERSION_TAG"
        fi
    else
        # Get changes since last tag
        LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        if [ -n "$LAST_TAG" ]; then
            RANGE="$LAST_TAG..HEAD"
        else
            RANGE="HEAD"
        fi
    fi

    CHANGELOG_CONTENT=$(git log --oneline --pretty=format:"%h %s" "$RANGE" | \
        python3 -c "
import sys
from datetime import datetime
import re

lines = sys.stdin.read().strip().split('\n')
if not lines or lines == ['']:
    print('No changes found.')
    sys.exit(0)

# Categorize commits
sections = {
    'Features': [],
    'Bug Fixes': [],
    'Documentation': [],
    'Performance': [],
    'Refactoring': [],
    'Testing': [],
    'Build System': [],
    'Other': []
}

for line in lines:
    if not line.strip():
        continue

    parts = line.split(' ', 1)
    if len(parts) < 2:
        continue

    commit_hash = parts[0]
    subject = parts[1]

    # Categorize based on conventional commit types
    if re.match(r'^feat(\(.+\))?:', subject):
        sections['Features'].append(f'- {subject} ({commit_hash})')
    elif re.match(r'^fix(\(.+\))?:', subject):
        sections['Bug Fixes'].append(f'- {subject} ({commit_hash})')
    elif re.match(r'^docs(\(.+\))?:', subject):
        sections['Documentation'].append(f'- {subject} ({commit_hash})')
    elif re.match(r'^perf(\(.+\))?:', subject):
        sections['Performance'].append(f'- {subject} ({commit_hash})')
    elif re.match(r'^refactor(\(.+\))?:', subject):
        sections['Refactoring'].append(f'- {subject} ({commit_hash})')
    elif re.match(r'^test(\(.+\))?:', subject):
        sections['Testing'].append(f'- {subject} ({commit_hash})')
    elif re.match(r'^(build|ci|chore)(\(.+\))?:', subject):
        sections['Build System'].append(f'- {subject} ({commit_hash})')
    else:
        sections['Other'].append(f'- {subject} ({commit_hash})')

# Generate output
version_name = '$NEW_VERSION' if '$NEW_VERSION' != 'Unreleased' else 'Unreleased'
date_str = datetime.now().strftime('%Y-%m-%d')

print(f'## [{version_name}] - {date_str}')
print('')

for section_name, commits in sections.items():
    if commits:
        print(f'### {section_name}')
        print('')
        for commit in commits:
            print(commit)
        print('')

if not any(sections.values()):
    print('No categorized changes found.')
")
fi

# Clean up temp config
rm -f "$TEMP_CONFIG"

# Output or write changelog
if [ "$PREVIEW_MODE" = true ]; then
    echo "Changelog preview:"
    echo "=================="
    echo "$CHANGELOG_CONTENT"
else
    # Check if CHANGELOG.md exists
    if [ -f "$CHANGELOG_FILE" ]; then
        # Prepend new content to existing changelog
        echo "Updating existing $CHANGELOG_FILE..."

        # Create backup
        cp "$CHANGELOG_FILE" "${CHANGELOG_FILE}.bak"

        # Create new changelog with new content at top
        {
            echo "$CHANGELOG_CONTENT"
            echo ""
            # Skip the first few lines of the old changelog (header and first entry)
            tail -n +4 "$CHANGELOG_FILE" 2>/dev/null || cat "$CHANGELOG_FILE"
        } > "${CHANGELOG_FILE}.new"

        mv "${CHANGELOG_FILE}.new" "$CHANGELOG_FILE"
        echo "✓ Updated $CHANGELOG_FILE"
    else
        # Create new changelog
        echo "Creating new $CHANGELOG_FILE..."
        {
            echo "# Changelog"
            echo ""
            echo "All notable changes to this project will be documented in this file."
            echo ""
            echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
            echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
            echo ""
            echo "$CHANGELOG_CONTENT"
        } > "$CHANGELOG_FILE"
        echo "✓ Created $CHANGELOG_FILE"
    fi

    # If in release mode, create git tag
    if [ "$RELEASE_MODE" = true ] && [ "$VERSION_TAG" != "Unreleased" ]; then
        echo ""
        echo "Creating git tag: $VERSION_TAG"
        if git tag -a "$VERSION_TAG" -m "Release $VERSION_TAG"; then
            echo "✓ Created tag $VERSION_TAG"
            echo ""
            echo "To publish this release:"
            echo "  git push origin main"
            echo "  git push origin $VERSION_TAG"
        else
            echo "Warning: Failed to create tag (may already exist)"
        fi
    fi
fi

echo ""
echo "========================================="
echo "Changelog generation completed!"
echo "========================================="

if [ "$PREVIEW_MODE" = false ]; then
    echo ""
    echo "Next steps:"
    echo "  1. Review $CHANGELOG_FILE"
    echo "  2. Commit changes: git add $CHANGELOG_FILE $VERSION_FILE && git commit -m 'chore: update changelog'"
    if [ "$RELEASE_MODE" = true ]; then
        echo "  3. Push release: git push origin main && git push origin $VERSION_TAG"
    fi
fi