#!/bin/bash
#
# CHIP Workbench Runner
#
# Usage:
#   ./run.sh <script>              Run a script (e.g., coverage, timeseries)
#   ./run.sh <script> -v           Run script and view report
#   ./run.sh --view <script>       View last report for script
#   ./run.sh --view <path>         View specific report file
#   ./run.sh --list                List available scripts
#
# Examples:
#   ./run.sh coverage              Run coverage analysis
#   ./run.sh coverage -v           Run and view report
#   ./run.sh --view coverage       View last coverage report
#   ./run.sh --view output/reports/coverage_20260201.md
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"
REPORTS_DIR="$SCRIPT_DIR/output/reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------

show_help() {
    echo "CHIP Workbench Runner"
    echo ""
    echo "Usage:"
    echo "  ./run.sh <script>              Run a script"
    echo "  ./run.sh <script> -v           Run script and view report"
    echo "  ./run.sh --view <script>       View last report for script"
    echo "  ./run.sh --view <path>         View specific report file"
    echo "  ./run.sh --list                List available scripts"
    echo ""
    echo "Scripts:"
    list_scripts
}

list_scripts() {
    for f in "$SCRIPTS_DIR"/*.py; do
        if [[ -f "$f" && "$(basename "$f")" != "__init__.py" ]]; then
            name=$(basename "$f" .py)
            # Extract first line of docstring as description
            desc=$("$VENV_PYTHON" -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
try:
    from scripts import $name
    doc = ${name}.__doc__ or ''
    # Get purpose line
    for line in doc.split('\n'):
        line = line.strip()
        if line.startswith('Purpose:'):
            continue
        if line and not line.startswith('Usage:') and not line.startswith('Outputs:'):
            print(line[:60])
            break
except:
    print('(no description)')
" 2>/dev/null || echo "(no description)")
            printf "  %-20s %s\n" "$name" "$desc"
        fi
    done
}

view_report() {
    local report="$1"
    
    if [[ ! -f "$report" ]]; then
        echo -e "${RED}Report not found: $report${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Viewing: $report${NC}"
    echo ""
    
    # Try viewers in order of preference
    # -p enables paging for long documents
    if command -v glow &>/dev/null; then
        exec glow -p "$report"
    elif command -v mdcat &>/dev/null; then
        # mdcat with pager
        mdcat "$report" | less -R
    elif command -v bat &>/dev/null; then
        exec bat --paging=always --language=markdown "$report"
    else
        # Fallback: less with the raw file
        less "$report"
    fi
}

find_latest_report() {
    local script_name="$1"
    local pattern="${script_name}_*.md"
    
    # Find most recent report matching pattern
    local latest=$(ls -t "$REPORTS_DIR"/$pattern 2>/dev/null | head -1)
    
    if [[ -z "$latest" ]]; then
        echo -e "${RED}No reports found for: $script_name${NC}"
        echo "Reports directory: $REPORTS_DIR"
        exit 1
    fi
    
    echo "$latest"
}

run_script() {
    local script_name="$1"
    local script_path="$SCRIPTS_DIR/${script_name}.py"
    
    if [[ ! -f "$script_path" ]]; then
        echo -e "${RED}Script not found: $script_name${NC}"
        echo ""
        echo "Available scripts:"
        list_scripts
        exit 1
    fi
    
    # Check venv exists
    if [[ ! -f "$VENV_PYTHON" ]]; then
        echo -e "${RED}Virtual environment not found.${NC}"
        echo "Run: make setup"
        exit 1
    fi
    
    echo -e "${GREEN}Running: $script_name${NC}"
    echo ""
    
    # Run the script
    "$VENV_PYTHON" "$script_path"
    
    echo ""
    
    # Find and report the output file
    local report=$(find_latest_report "$script_name" 2>/dev/null || true)
    if [[ -n "$report" && -f "$report" ]]; then
        echo -e "${GREEN}Report saved: $report${NC}"
        echo "$report"  # Output path for programmatic use
    fi
}

#------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------

# No arguments - show help
if [[ $# -eq 0 ]]; then
    show_help
    exit 0
fi

# Parse arguments
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    
    --list)
        echo "Available scripts:"
        list_scripts
        exit 0
        ;;
    
    --view)
        # View mode
        if [[ -z "$2" ]]; then
            echo -e "${RED}Usage: ./run.sh --view <script|path>${NC}"
            exit 1
        fi
        
        # Check if it's a file path or script name
        if [[ -f "$2" ]]; then
            # It's a file path
            view_report "$2"
        elif [[ -f "$REPORTS_DIR/$2" ]]; then
            # It's a filename in reports dir
            view_report "$REPORTS_DIR/$2"
        else
            # Assume it's a script name, find latest report
            report=$(find_latest_report "$2")
            view_report "$report"
        fi
        ;;
    
    *)
        # Run mode
        SCRIPT_NAME="$1"
        VIEW_AFTER=false
        
        if [[ "$2" == "-v" || "$2" == "--view" ]]; then
            VIEW_AFTER=true
        fi
        
        run_script "$SCRIPT_NAME"
        
        if $VIEW_AFTER; then
            echo ""
            report=$(find_latest_report "$SCRIPT_NAME")
            view_report "$report"
        fi
        ;;
esac
