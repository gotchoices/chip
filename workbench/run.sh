#!/bin/bash
#
# CHIP Workbench Runner
#
# Usage:
#   ./run.sh <study>              Run a study (e.g., coverage, timeseries)
#   ./run.sh <study> -v           Run study and view report
#   ./run.sh --view <study>       View last report for study
#   ./run.sh --view <path>        View specific report file
#   ./run.sh --pdf <study>        Generate PDF from study's FINDINGS.md
#   ./run.sh --list               List available studies
#
# Examples:
#   ./run.sh coverage              Run coverage analysis
#   ./run.sh coverage -v           Run and view report
#   ./run.sh --view coverage       View last coverage report
#   ./run.sh --pdf timeseries      Generate timeseries FINDINGS.pdf
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
STUDIES_DIR="$SCRIPT_DIR/studies"

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
    echo "  ./run.sh <study>              Run a study"
    echo "  ./run.sh <study> -v           Run study and view report"
    echo "  ./run.sh --view <study>       View last report for study"
    echo "  ./run.sh --view <path>        View specific report file"
    echo "  ./run.sh --pdf <study>        Generate PDF from FINDINGS.md"
    echo "  ./run.sh --list               List available studies"
    echo ""
    echo "Studies:"
    list_studies
}

list_studies() {
    for d in "$STUDIES_DIR"/*/; do
        if [[ -f "$d/study.py" ]]; then
            name=$(basename "$d")
            # Extract first non-empty docstring line as description
            desc=$("$VENV_PYTHON" -c "
import ast, sys
try:
    with open('$d/study.py') as f:
        tree = ast.parse(f.read())
    doc = ast.get_docstring(tree) or ''
    for line in doc.split('\n'):
        line = line.strip()
        if line and not line.startswith('Purpose:') and not line.startswith('Usage:') and not line.startswith('Outputs:'):
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
    local study_name="$1"
    local reports_dir="$STUDIES_DIR/$study_name/output/reports"
    local pattern="${study_name}_*.md"
    
    # Find most recent report matching pattern
    local latest=$(ls -t "$reports_dir"/$pattern 2>/dev/null | head -1)
    
    if [[ -z "$latest" ]]; then
        echo -e "${RED}No reports found for: $study_name${NC}"
        echo "Reports directory: $reports_dir"
        exit 1
    fi
    
    echo "$latest"
}

generate_pdf() {
    local study_name="$1"
    local study_dir="$STUDIES_DIR/$study_name"
    local findings="$study_dir/FINDINGS.md"
    local output_pdf="$study_dir/FINDINGS.pdf"
    
    if [[ ! -d "$study_dir" ]]; then
        echo -e "${RED}Study not found: $study_name${NC}"
        exit 1
    fi
    
    if [[ ! -f "$findings" ]]; then
        echo -e "${RED}No FINDINGS.md in: $study_dir${NC}"
        exit 1
    fi
    
    if ! command -v pandoc &>/dev/null; then
        echo -e "${RED}pandoc is required for PDF generation.${NC}"
        echo "Install with: brew install pandoc"
        echo ""
        echo "For best results, also install a LaTeX engine:"
        echo "  brew install --cask basictex   # minimal LaTeX"
        echo "  # or: brew install --cask mactex  # full LaTeX"
        exit 1
    fi
    
    echo -e "${BLUE}Generating PDF: $output_pdf${NC}"
    
    # Run pandoc from the study directory so relative image paths resolve
    if command -v xelatex &>/dev/null || command -v pdflatex &>/dev/null; then
        # LaTeX available — best quality
        local engine="pdflatex"
        command -v xelatex &>/dev/null && engine="xelatex"
        
        (cd "$study_dir" && pandoc FINDINGS.md -o FINDINGS.pdf \
            --pdf-engine="$engine" \
            -V geometry:margin=1in \
            -V colorlinks=true \
            -V linkcolor=blue \
            --standalone)
    elif command -v wkhtmltopdf &>/dev/null; then
        # HTML-to-PDF fallback
        (cd "$study_dir" && pandoc FINDINGS.md -t html5 --standalone | \
            wkhtmltopdf --enable-local-file-access - FINDINGS.pdf)
    else
        echo -e "${YELLOW}No LaTeX or wkhtmltopdf found. Trying pandoc default...${NC}"
        echo "For best results, install LaTeX: brew install --cask basictex"
        (cd "$study_dir" && pandoc FINDINGS.md -o FINDINGS.pdf \
            --standalone) || {
            echo -e "${RED}PDF generation failed.${NC}"
            echo "Install a PDF engine: brew install --cask basictex"
            exit 1
        }
    fi
    
    if [[ -f "$output_pdf" ]]; then
        echo -e "${GREEN}PDF saved: $output_pdf${NC}"
    else
        echo -e "${RED}PDF generation failed — no output file created.${NC}"
        exit 1
    fi
}

run_study() {
    local study_name="$1"
    local study_dir="$STUDIES_DIR/$study_name"
    local study_script="$study_dir/study.py"
    
    if [[ ! -f "$study_script" ]]; then
        echo -e "${RED}Study not found: $study_name${NC}"
        echo ""
        echo "Available studies:"
        list_studies
        exit 1
    fi
    
    # Check venv exists
    if [[ ! -f "$VENV_PYTHON" ]]; then
        echo -e "${RED}Virtual environment not found.${NC}"
        echo "Run: make setup"
        exit 1
    fi
    
    echo -e "${GREEN}Running: $study_name${NC}"
    echo ""
    
    # Run the study script
    "$VENV_PYTHON" "$study_script"
    
    echo ""
    
    # Find and report the output file
    local report=$(find_latest_report "$study_name" 2>/dev/null || true)
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
        echo "Available studies:"
        list_studies
        exit 0
        ;;
    
    --pdf)
        # PDF generation mode
        if [[ -z "$2" ]]; then
            echo -e "${RED}Usage: ./run.sh --pdf <study>${NC}"
            exit 1
        fi
        generate_pdf "$2"
        ;;
    
    --view)
        # View mode
        if [[ -z "$2" ]]; then
            echo -e "${RED}Usage: ./run.sh --view <study|path>${NC}"
            exit 1
        fi
        
        # Check if it's a file path or study name
        if [[ -f "$2" ]]; then
            # It's a file path
            view_report "$2"
        elif [[ -f "$STUDIES_DIR/$2/output/reports/$2" ]]; then
            # It's a filename in the study's reports dir
            view_report "$STUDIES_DIR/$2/output/reports/$2"
        else
            # Assume it's a study name, find latest report
            report=$(find_latest_report "$2")
            view_report "$report"
        fi
        ;;
    
    *)
        # Run mode
        STUDY_NAME="$1"
        VIEW_AFTER=false
        
        if [[ "$2" == "-v" || "$2" == "--view" ]]; then
            VIEW_AFTER=true
        fi
        
        run_study "$STUDY_NAME"
        
        if $VIEW_AFTER; then
            echo ""
            report=$(find_latest_report "$STUDY_NAME")
            view_report "$report"
        fi
        ;;
esac
