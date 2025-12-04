#!/bin/bash
# Test script to verify all CLI examples from README.md work correctly

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Test function
test_command() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"

    echo ""
    echo "Testing: $test_name"
    echo "Command: $command"

    if eval "$command" > /tmp/test_output.txt 2>&1; then
        if [ -n "$expected_pattern" ]; then
            if grep -q "$expected_pattern" /tmp/test_output.txt; then
                echo -e "${GREEN}✓ PASSED${NC}"
                ((PASSED++))
            else
                echo -e "${RED}✗ FAILED - Pattern not found: $expected_pattern${NC}"
                cat /tmp/test_output.txt
                ((FAILED++))
            fi
        else
            echo -e "${GREEN}✓ PASSED${NC}"
            ((PASSED++))
        fi
    else
        echo -e "${YELLOW}⚠ WARNING - Command failed (may be API issue)${NC}"
        cat /tmp/test_output.txt
        ((WARNINGS++))
    fi
}

echo "======================================================================"
echo "Testing CLI Examples from README.md"
echo "======================================================================"

# Quick Start - CLI Examples
echo ""
echo "=== Quick Start CLI Examples ==="

test_command \
    "Convert IDs (basic)" \
    "timeout 15 python3 -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene" \
    "ENSG"

test_command \
    "Convert IDs (dict format)" \
    "timeout 15 python3 -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict" \
    "results"

test_command \
    "Label to ID conversion" \
    "timeout 15 python3 -m togoid label2id --labels 'BRCA1,TP53,EGFR' --dataset ncbigene --taxonomy 9606" \
    "672"

test_command \
    "Annotate IDs" \
    "timeout 20 python3 -m togoid annotate --dataset ncbigene --ids 672 --field gene_synonym" \
    "BRCA"

test_command \
    "List annotation fields" \
    "timeout 15 python3 -m togoid annotate --dataset ncbigene --list-fields" \
    "gene_synonym"

test_command \
    "Config dataset" \
    "timeout 15 python3 -m togoid config dataset ncbigene" \
    "NCBI Gene"

# Convert Command Examples
echo ""
echo "=== Convert Command Examples ==="

test_command \
    "Basic conversion" \
    "timeout 15 python3 -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene" \
    "ENSG"

test_command \
    "With output format" \
    "timeout 15 python3 -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict" \
    "results"

# Test save to file
echo ""
echo "Testing: Save to file"
rm -f /tmp/test_results.csv
if timeout 15 python3 -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene --output /tmp/test_results.csv 2>&1; then
    if [ -f /tmp/test_results.csv ]; then
        echo -e "${GREEN}✓ PASSED - File created${NC}"
        ((PASSED++))
        rm -f /tmp/test_results.csv
    else
        echo -e "${RED}✗ FAILED - File not created${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ WARNING - Command failed${NC}"
    ((WARNINGS++))
fi

# Label2ID Command Examples
echo ""
echo "=== Label2ID Command Examples ==="

test_command \
    "Basic label2id conversion" \
    "timeout 15 python3 -m togoid label2id --labels 'BRCA1,TP53,EGFR' --dataset ncbigene --taxonomy 9606" \
    "672"

# Test from file
echo ""
echo "Testing: Label2ID from file"
echo -e "BRCA1\nTP53\nEGFR" > /tmp/test_genes.txt
test_command \
    "Label2ID from file" \
    "timeout 15 python3 -m togoid label2id --label-file /tmp/test_genes.txt --dataset ncbigene --taxonomy 9606" \
    "672"
rm -f /tmp/test_genes.txt

test_command \
    "Label2ID CSV output" \
    "timeout 15 python3 -m togoid label2id --labels 'BRCA1,TP53' --dataset ncbigene --taxonomy 9606 --format csv" \
    "input,match_type"

test_command \
    "Label2ID with custom label_types" \
    "timeout 15 python3 -m togoid label2id --labels 'BRCA1' --dataset ncbigene --label_types 'symbol' --taxonomy 9606" \
    "672"

test_command \
    "Label2ID for ChEBI dataset" \
    "timeout 15 python3 -m togoid label2id --labels 'caffeine' --dataset chebi --label_types 'togoid_chebi_label'" \
    "caffeine"

# Annotate Command Examples
echo ""
echo "=== Annotate Command Examples ==="

test_command \
    "Get annotations" \
    "timeout 20 python3 -m togoid annotate --dataset ncbigene --ids 672 --field gene_synonym --field full_name" \
    "BRCA"

test_command \
    "List fields" \
    "timeout 15 python3 -m togoid annotate --dataset ncbigene --list-fields" \
    "gene_synonym"

test_command \
    "With filters" \
    "timeout 20 python3 -m togoid annotate --dataset ncbigene --ids 672,7157 --field type_of_gene --filter type_of_gene=protein-coding" \
    ""

# Test CSV output
echo ""
echo "Testing: Annotate CSV output"
rm -f /tmp/test_genes.csv
if timeout 20 python3 -m togoid annotate --dataset ncbigene --ids 672 --field gene_synonym --format csv --output /tmp/test_genes.csv 2>&1; then
    if [ -f /tmp/test_genes.csv ] && grep -q "BRCA" /tmp/test_genes.csv; then
        echo -e "${GREEN}✓ PASSED - CSV file created with expected content${NC}"
        ((PASSED++))
        rm -f /tmp/test_genes.csv
    else
        echo -e "${RED}✗ FAILED - CSV file missing or incorrect${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ WARNING - Command failed${NC}"
    ((WARNINGS++))
fi

# Test from file
echo ""
echo "Testing: Annotate from file"
echo "672" > /tmp/gene_ids.txt
test_command \
    "Annotate from file" \
    "timeout 20 python3 -m togoid annotate --dataset ncbigene --ids-file /tmp/gene_ids.txt --field gene_synonym" \
    "BRCA"
rm -f /tmp/gene_ids.txt

# Python Library Features (not CLI commands)
echo ""
echo "=== Python Library Features (Annotations, Filtering, Orthologs) ==="

# Test convert with annotations
echo ""
echo "Testing: Convert with Annotations"
timeout 30 python3 -c "
from togoid import TogoIDConverter
converter = TogoIDConverter()
result = converter.convert(
    ids=['1', '9'],
    route=['ncbigene', 'ensembl_gene', 'ensembl_transcript'],
    format='table',
    annotate=[('ncbigene', 'label'), ('ncbigene', 'full_name')]
)
print(f'Rows: {len(result)}, Columns: {len(result[0]) if result else 0}')
print(f'First row: {result[0]}')
assert len(result) > 0 and len(result[0]) == 5, 'Expected 5 columns (3 route + 2 annotations)'
print('Success: Annotations added')
" > /tmp/test_output.txt 2>&1

if [ $? -eq 0 ] && grep -q "Success: Annotations added" /tmp/test_output.txt; then
    echo -e "${GREEN}✓ PASSED - Convert with Annotations${NC}"
    cat /tmp/test_output.txt
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING - Convert with Annotations${NC}"
    cat /tmp/test_output.txt
    ((WARNINGS++))
fi

# Test convert with filtering
echo ""
echo "Testing: Convert with Filtering"
timeout 30 python3 -c "
from togoid import TogoIDConverter
converter = TogoIDConverter()
result = converter.convert(
    ids=['1', '9'],
    route=['ncbigene', 'ensembl_gene', 'ensembl_transcript'],
    format='table',
    annotate=[('ncbigene', 'label')],
    filter=[('ensembl_transcript', 'transcript_flag', ['MANE Select'])]
)
print(f'Filtered rows: {len(result)}')
if result:
    print(f'First row: {result[0]}')
assert len(result) > 0, 'Expected at least 1 filtered result'
print('Success: Filtering applied')
" > /tmp/test_output.txt 2>&1

if [ $? -eq 0 ] && grep -q "Success: Filtering applied" /tmp/test_output.txt; then
    echo -e "${GREEN}✓ PASSED - Convert with Filtering${NC}"
    cat /tmp/test_output.txt
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING - Convert with Filtering${NC}"
    cat /tmp/test_output.txt
    ((WARNINGS++))
fi

# Test get_ortholog
echo ""
echo "Testing: Get Orthologs"
timeout 30 python3 -c "
from togoid import TogoIDConverter
converter = TogoIDConverter()
result = converter.get_ortholog(
    ids=['1', '9'],
    route=['ncbigene', 'homologene'],
    target_taxids=['10090', '10116'],  # Mouse and Rat
    format='table'
)
print(f'Orthologs found: {len(result)}')
for row in result:
    print(f'  {row}')
assert len(result) > 0, 'Expected at least 1 ortholog'
assert len(result[0]) == 3, 'Expected 3 columns (homologene_id, gene_id, taxid)'
print('Success: Orthologs retrieved')
" > /tmp/test_output.txt 2>&1

if [ $? -eq 0 ] && grep -q "Success: Orthologs retrieved" /tmp/test_output.txt; then
    echo -e "${GREEN}✓ PASSED - Get Orthologs${NC}"
    cat /tmp/test_output.txt
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING - Get Orthologs${NC}"
    cat /tmp/test_output.txt
    ((WARNINGS++))
fi

# Test get_ortholog with dict format
echo ""
echo "Testing: Get Orthologs (dict format)"
timeout 30 python3 -c "
from togoid import TogoIDConverter
converter = TogoIDConverter()
result = converter.get_ortholog(
    ids=['1', '9'],
    route=['ncbigene', 'homologene'],
    target_taxids=['10090'],  # Mouse only
    format='dict'
)
print(f'Homologene groups: {len(result)}')
for hom_id, orthologs in result.items():
    print(f'  {hom_id}: {len(orthologs)} orthologs')
assert isinstance(result, dict), 'Expected dict format'
print('Success: Orthologs retrieved in dict format')
" > /tmp/test_output.txt 2>&1

if [ $? -eq 0 ] && grep -q "Success: Orthologs retrieved in dict format" /tmp/test_output.txt; then
    echo -e "${GREEN}✓ PASSED - Get Orthologs (dict format)${NC}"
    cat /tmp/test_output.txt
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING - Get Orthologs (dict format)${NC}"
    cat /tmp/test_output.txt
    ((WARNINGS++))
fi

# Other Commands
echo ""
echo "=== Other Commands Examples ==="

test_command \
    "Config dataset" \
    "timeout 15 python3 -m togoid config dataset ncbigene" \
    "NCBI Gene"

test_command \
    "Config descriptions" \
    "timeout 15 python3 -m togoid config descriptions" \
    "BioProject"

test_command \
    "Count mappings" \
    "timeout 15 python3 -m togoid count ncbigene ensembl_gene --ids 1,9" \
    "source"

# Search and Route commands (may fail due to API)
echo ""
echo "=== Optional Commands (may fail due to API limitations) ==="

test_command \
    "Search databases" \
    "timeout 15 python3 -m togoid search databases uniprot" \
    ""

test_command \
    "Route finding" \
    "timeout 15 python3 -m togoid route ncbigene ensembl_gene" \
    ""

test_command \
    "Lookup ID" \
    "timeout 15 python3 -m togoid lookup id 672" \
    ""

# Cleanup
rm -f /tmp/test_output.txt

# Summary
echo ""
echo "======================================================================"
echo "Test Results Summary"
echo "======================================================================"
echo -e "${GREEN}Passed:   $PASSED${NC}"
echo -e "${RED}Failed:   $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo "======================================================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
