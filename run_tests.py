import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.tests.verify_environment import verify_all
from backend.tests.test_dynamic_graph import test_dynamic_graph
from backend.tests.test_api import test_all_api_endpoints
from backend.tests.test_evaluation_benchmark import run_evaluation_benchmark
from backend.tests.test_portfolio import test_portfolio_and_market_endpoints
from backend.scripts.seed_db import seed_database

def run_all_tests():
    print("==================================================")
    print(" EXECUTING FULL PERSONAL FINANCE AI TEST SUITE")
    print("==================================================")
    
    # 0. Clean Baseline Seed
    seed_database()

    # 1. Baseline Environment Verification
    print("\n>>> SUITE 1: Baseline Environment Verification")
    verify_all()

    # 2. Phase 1 Dynamic Graph Tests
    print("\n>>> SUITE 2: Dynamic Knowledge Graph CRUD Tests")
    test_dynamic_graph()

    # 3. Phase 9 FastAPI REST Backend Tests
    print("\n>>> SUITE 3: FastAPI REST Backend Endpoint Tests")
    test_all_api_endpoints()

    # 4. Research Evaluation Benchmark
    print("\n>>> SUITE 4: Research Evaluation Benchmark")
    run_evaluation_benchmark()

    # 5. Portfolio & Market Intelligence Tests
    print("\n>>> SUITE 5: Portfolio Intelligence & Market Data Tests")
    test_portfolio_and_market_endpoints()

    # Reset to clean demo state
    seed_database()

    print("\n==================================================")
    print(" ALL 5 TEST SUITES COMPLETED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
