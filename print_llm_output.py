import argparse
from icd9_llm_tree_search.tree_search import ICD9LLMTreeSearch
from tqdm import tqdm
import re

parser = argparse.ArgumentParser(description="Print raw LLM output for a given note using ICD9LLMTreeSearch.")
parser.add_argument('--model_name', type=str, default='gpt-3.5-turbo', help='Model name (e.g., gpt-3.5-turbo, llama, etc.)')
parser.add_argument('--api_key', type=str, required=True, help='API key for OpenAI or LM Studio')
parser.add_argument('--base_url', type=str, default=None, help='Base URL for LM Studio or OpenAI-compatible endpoint')
parser.add_argument('--note', type=str, required=True, help='Clinical note to process')
parser.add_argument('--max_depth', type=int, default=7, help='Tree search depth (default: 7)')
args = parser.parse_args()

searcher = ICD9LLMTreeSearch(model_name=args.model_name, api_key=args.api_key, base_url=args.base_url)

stack = [(searcher.icd9, 0)]
visited = set()
pbar = tqdm(total=args.max_depth, desc="Tree Search Depth", unit="level")
current_depth = 0

def is_yes_for_code(code, output):
    pattern = re.compile(rf"^{re.escape(code)}[^\n]*yes", re.IGNORECASE | re.MULTILINE)
    return bool(pattern.search(output))

while stack:
    node, depth = stack.pop()
    if depth > args.max_depth:
        continue
    if (node.code, depth) in visited:
        continue
    visited.add((node.code, depth))
    if depth > current_depth:
        pbar.update(depth - current_depth)
        current_depth = depth
    children = node.children
    if not children:
        continue
    print(f"\n=== Exploring depth {depth}, parent code: {node.code} ===")
    print("Codes being explored:")
    for child in children:
        print(f"  {child.code}: {child.description}")
    raw_output = searcher._llm_decide(args.note, children)
    print("\n=== RAW LLM OUTPUT ===\n")
    print(raw_output)
    for child in children:
        if is_yes_for_code(child.code, raw_output):
            stack.append((child, depth+1))
pbar.update(args.max_depth - current_depth)
pbar.close() 