
import uuid     
import json    
import logging  
from pprint import pprint  # Pretty-prints data structures (unused here, but available)



from dotenv import load_dotenv
load_dotenv(override=True) 

from backend.src.graph.workflow import app
logging.basicConfig(
    level=logging.INFO,       
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
    # Example: "2024-01-15 10:30:45 - brand-guardian - INFO - Starting audit"
)
logger = logging.getLogger("brand-guardian-runner")  # Creates a named logger for this module


def run_cli_simulation():
    """
    Simulates a Video Compliance Audit request.
    
    This function orchestrates the entire audit process:
    - Creates a unique session ID
    - Prepares the video URL and metadata
    - Runs it through the AI workflow
    - Displays the compliance results
    """
    
 
    session_id = str(uuid.uuid4())  
    logger.info(f"Starting Audit Session: {session_id}")  

    initial_inputs = {
        # The YouTube video to audit
        "video_url": "https://youtu.be/dT7S75eYhcQ",
        
       
        "video_id": f"vid_{session_id[:8]}",
        
        "compliance_results": [],
        "errors": []
    }

    # ========== DISPLAY SECTION: INPUT SUMMARY ==========
    print("\n--- 1.nput Payload: INITIALIZING WORKFLOW ---")
    print(f"I {json.dumps(initial_inputs, indent=2)}")

    # ========== STEP 3: EXECUTE GRAPH ==========
    # This is where the magic happens - runs the entire workflow
    try:
       
        final_state = app.invoke(initial_inputs)
        
        # ========== DISPLAY SECTION: EXECUTION COMPLETE ==========
        print("\n--- 2. WORKFLOW EXECUTION COMPLETE ---")
        
        # ========== STEP 4: OUTPUT RESULTS ==========
        # Display a formatted compliance report
        
        print("\n=== COMPLIANCE AUDIT REPORT ===")
        
        # .get() safely retrieves values (returns None if key doesn't exist)
        # Displays the video ID that was audited
        print(f"Video ID:    {final_state.get('video_id')}")
        
        # Shows PASS or FAIL status
        print(f"Status:      {final_state.get('final_status')}")
        
        # ========== VIOLATIONS SECTION ==========
        print("\n[ VIOLATIONS DETECTED ]")
        
        # Extract the list of compliance violations
        # Default to empty list if no results
        results = final_state.get('compliance_results', [])
        
        if results:
            # Loop through each violation and display it
            for issue in results:
                # Each issue is a dict with: severity, category, description
                # Example output: "- [CRITICAL] Misleading Claims: Absolute guarantee detected"
                print(f"- [{issue.get('severity')}] {issue.get('category')}: {issue.get('description')}")
        else:
            # No violations found (clean video)
            print("No violations found.")

        # ========== SUMMARY SECTION ==========
        print("\n[ FINAL SUMMARY ]")
        # Displays the AI-generated natural language summary
        # Example: "Video contains 2 critical violations..."
        print(final_state.get('final_report'))

    except Exception as e:
        # ========== ERROR HANDLING ==========
        # If anything breaks, log the error
        logger.error(f"Workflow Execution Failed: {str(e)}")
        
        # Re-raise the exception so we see the full error traceback
        # This helps with debugging (shows exactly where/why it failed)
        raise e


# ========== PROGRAM ENTRY POINT ==========
# This block only runs when you execute: python main.py
# It won't run if you import this file as a module
if __name__ == "__main__":
    run_cli_simulation()  # Start the compliance audit simulation



'''
You have moved from "Coding" to "Product."

Ingestion:  (YouTube -> Azure)

Indexing:  (Speech-to-Text + OCR)

Retrieval:  (Found the rules about "Claims")

Reasoning:  (Applied rules to the specific claims in the video)

You are done. Your pipeline is fully operational.
'''