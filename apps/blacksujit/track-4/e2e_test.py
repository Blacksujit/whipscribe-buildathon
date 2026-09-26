import os
import sys
import time
import json
from dotenv import load_dotenv

# Add src directory to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.api.whip_api import submit_file, poll_job, get_transcript
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.database.store import init_db, save_evaluation, get_evaluation_dicts_for_comparison

load_dotenv()

def test_e2e():
    print("🚀 Starting E2E Integration Test...")
    
    init_db()
    api_key = os.environ.get("WHIPSKRIBE_API_KEY")
    llm_provider = os.environ.get("LLM_PROVIDER", "groq")
    llm_api_key = (
        os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    llm_model = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
    
    if not api_key:
        print("❌ Missing WHIPSKRIBE_API_KEY")
        return False

    file_path = "src/test_audio.wav"
    if not os.path.exists(file_path):
        print(f"❌ Test file not found: {file_path}")
        return False
        
    print(f"Uploading {file_path}...")
    upload_res = submit_file(api_key, file_path)
    if not upload_res:
        print("❌ Upload failed: No job ID returned")
        return False
    job_id = upload_res
    print(f"Job created: {job_id}")

    print("Polling for completion (blocking)...")
    try:
        poll_job(api_key, job_id)
    except Exception as e:
        print(f"❌ Polling failed: {e}")
        return False

    print("Fetching transcript...")
    transcript = get_transcript(api_key, job_id)
    if not transcript:
        print("❌ Failed to fetch transcript")
        return False

    print("Running Multi-Agent Evaluation...")
    eval_result = evaluate(transcript, llm_api_key, llm_model, llm_provider)
    if not eval_result["success"]:
        print("❌ Evaluation failed")
        return False
    print(f"Evaluation Score: {eval_result['evaluation']['overall_score']}")

    print("Saving to DB...")
    save_evaluation(job_id, transcript, eval_result["evaluation"], "E2E Test Call")
    
    print("Testing Trend Analysis...")
    evals, names = get_evaluation_dicts_for_comparison()
    if len(evals) > 0:
        comparison = compare_evaluations(evals, names)
        print(f"Deal Velocity: {comparison['deal_velocity']['velocity']}")
    else:
        print("⚠️ No evaluations found for comparison")

    print("\n✅ E2E Test Passed Successfully!")
    return True

if __name__ == "__main__":
    try:
        test_e2e()
    except Exception as e:
        print(f"❌ E2E Test crashed: {e}")
        import traceback
        traceback.print_exc()
