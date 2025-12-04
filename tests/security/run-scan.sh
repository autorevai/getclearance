#!/bin/bash
#
# Get Clearance - Security Scan Script
# =====================================
# Runs OWASP ZAP security scan against the API.
#
# Usage:
#   ./run-scan.sh                    # Scan localhost
#   ./run-scan.sh https://api.url    # Scan specific URL
#

set -e

# Configuration
TARGET_URL="${1:-http://localhost:8000}"
REPORT_DIR="$(dirname "$0")/reports"
OPENAPI_URL="${TARGET_URL}/openapi.json"

echo "============================================"
echo "Get Clearance Security Scan"
echo "============================================"
echo "Target: ${TARGET_URL}"
echo "OpenAPI: ${OPENAPI_URL}"
echo "Reports: ${REPORT_DIR}"
echo "============================================"

# Create reports directory
mkdir -p "${REPORT_DIR}"

# Check if ZAP is available
if ! command -v zap-cli &> /dev/null && ! command -v docker &> /dev/null; then
    echo "Error: Neither zap-cli nor Docker found."
    echo "Install OWASP ZAP or Docker to run security scans."
    echo ""
    echo "Install options:"
    echo "  - Homebrew: brew install zaproxy"
    echo "  - Docker: docker pull owasp/zap2docker-stable"
    exit 1
fi

# Run with Docker if available
if command -v docker &> /dev/null; then
    echo "Running OWASP ZAP API scan with Docker..."

    docker run --rm \
        --network host \
        -v "$(pwd):/zap/wrk/:rw" \
        -t owasp/zap2docker-stable \
        zap-api-scan.py \
        -t "${OPENAPI_URL}" \
        -f openapi \
        -r "reports/zap-report.html" \
        -J "reports/zap-report.json" \
        -w "reports/zap-report.md" \
        -c "zap-config.yaml" \
        -I

    echo ""
    echo "Scan complete!"
    echo "Reports saved to:"
    echo "  - ${REPORT_DIR}/zap-report.html"
    echo "  - ${REPORT_DIR}/zap-report.json"
    echo "  - ${REPORT_DIR}/zap-report.md"
else
    # Fallback to local ZAP installation
    echo "Running OWASP ZAP with local installation..."

    zap-cli --zap-path /Applications/OWASP\ ZAP.app/Contents/MacOS/OWASP\ ZAP.sh \
        quick-scan \
        --self-contained \
        --spider \
        --ajax-spider \
        --recursive \
        "${TARGET_URL}"
fi

echo ""
echo "============================================"
echo "Security Scan Summary"
echo "============================================"

# Parse results if JSON report exists
if [ -f "${REPORT_DIR}/zap-report.json" ]; then
    # Count alerts by risk level
    if command -v jq &> /dev/null; then
        HIGH=$(jq '[.site[].alerts[] | select(.riskcode == "3")] | length' "${REPORT_DIR}/zap-report.json" 2>/dev/null || echo "0")
        MEDIUM=$(jq '[.site[].alerts[] | select(.riskcode == "2")] | length' "${REPORT_DIR}/zap-report.json" 2>/dev/null || echo "0")
        LOW=$(jq '[.site[].alerts[] | select(.riskcode == "1")] | length' "${REPORT_DIR}/zap-report.json" 2>/dev/null || echo "0")
        INFO=$(jq '[.site[].alerts[] | select(.riskcode == "0")] | length' "${REPORT_DIR}/zap-report.json" 2>/dev/null || echo "0")

        echo "High Risk:   ${HIGH}"
        echo "Medium Risk: ${MEDIUM}"
        echo "Low Risk:    ${LOW}"
        echo "Info:        ${INFO}"

        # Fail if high-risk vulnerabilities found
        if [ "${HIGH}" -gt 0 ]; then
            echo ""
            echo "ERROR: High-risk vulnerabilities found!"
            exit 1
        fi
    else
        echo "Install jq for detailed results: brew install jq"
    fi
fi

echo ""
echo "Done!"
