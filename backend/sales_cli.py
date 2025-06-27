#!/usr/bin/env python3
"""
Simple CLI for Sales Order Processing
Processes text files through the multi-agent workflow with detailed output at each step
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import argparse
import logging
from typing import Dict, Any, Optional

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.agents.workflow_state import WorkflowState, WorkflowStage
from app.agents.enhanced_order_extractor import EnhancedOrderExtractor
from app.agents.agentic_search_coordinator import AgenticSearchCoordinator
from app.agents.part_matching_agent import PartMatchingAgent
from app.agents.order_assembly_agent import OrderAssemblyAgent
from app.services.local_parts_catalog import LocalPartsCatalogService
from app.database.connection import get_db_manager
from app.core.config import settings
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_output.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleWorkflowProcessor:
    """Simple processor that runs documents through the agentic workflow"""
    
    def __init__(self, output_dir: str = "workflow_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize LLM
        if not settings.openai_api_key:
            logger.error("OpenAI API key not found! Set OPENAI_API_KEY environment variable.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0,
                openai_api_key=settings.openai_api_key
            )
        
        # Initialize agents
        self.order_extractor = EnhancedOrderExtractor(self.llm) if self.llm else None
        self.catalog_service = LocalPartsCatalogService()
        self.search_coordinator = AgenticSearchCoordinator(self.catalog_service, self.llm)
        self.matching_agent = PartMatchingAgent(self.llm) if self.llm else None
        self.assembly_agent = OrderAssemblyAgent(self.llm)
        
        logger.info("Workflow processor initialized")
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file through the workflow"""
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create session ID from filename and timestamp
        session_id = f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_output_dir = self.output_dir / session_id
        session_output_dir.mkdir(exist_ok=True)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"PROCESSING FILE: {file_path.name}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Output Directory: {session_output_dir}")
        logger.info(f"{'='*80}\n")
        
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Save input
        self._save_step_output(session_output_dir, "00_input.txt", content)
        
        # Initialize results
        results = {
            "session_id": session_id,
            "input_file": str(file_path),
            "start_time": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Document Analysis
            logger.info("STEP 1: Document Analysis")
            logger.info("-" * 40)
            doc_analysis = {
                "content_length": len(content),
                "preview": content[:500] + "..." if len(content) > 500 else content
            }
            self._save_step_output(session_output_dir, "01_document_analysis.json", doc_analysis)
            results["steps"]["document_analysis"] = doc_analysis
            logger.info(f"Content length: {doc_analysis['content_length']} characters")
            
            # Step 2: Order Extraction
            logger.info("\nSTEP 2: Order Extraction")
            logger.info("-" * 40)
            
            if self.order_extractor:
                extracted_order = await self.order_extractor.extract_order_with_line_items(
                    content, session_id
                )
                
                # Save extraction output
                extraction_output = {
                    "order_id": extracted_order.order_id,
                    "customer": extracted_order.order_metadata.customer,
                    "line_items_count": len(extracted_order.line_items),
                    "line_items": [
                        {
                            "line_id": item.line_id,
                            "raw_text": item.raw_text,
                            "extracted_specs": item.extracted_specs.dict() if item.extracted_specs else {}
                        }
                        for item in extracted_order.line_items
                    ]
                }
                self._save_step_output(session_output_dir, "02_extracted_order.json", extraction_output)
                results["steps"]["order_extraction"] = extraction_output
                
                logger.info(f"Customer: {extracted_order.order_metadata.customer}")
                logger.info(f"Extracted {len(extracted_order.line_items)} line items")
                for item in extracted_order.line_items:
                    logger.info(f"  - {item.line_id}: {item.raw_text[:100]}...")
            else:
                logger.error("Order extraction skipped - No LLM available")
                return results
            
            # Step 3: Parts Search
            logger.info("\nSTEP 3: Parts Search & Matching")
            logger.info("-" * 40)
            
            # Check catalog status
            stats = await self.catalog_service.get_catalog_stats()
            logger.info(f"Using catalog with {stats.get('total_parts', 0)} parts from database")
            
            search_results = {}
            matches = {}
            
            for i, line_item in enumerate(extracted_order.line_items):
                logger.info(f"\nSearching for line item {i+1}/{len(extracted_order.line_items)}: {line_item.line_id}")
                
                # Search for parts
                search_result = await self.search_coordinator.search_for_line_item(line_item)
                search_results[line_item.line_id] = [
                    {
                        "part_number": r.part_number if hasattr(r, 'part_number') else r.get("part_number", ""),
                        "description": r.description if hasattr(r, 'description') else r.get("description", ""),
                        "score": r.similarity_score if hasattr(r, 'similarity_score') else r.get("scores", {}).get("combined_score", 0)
                    }
                    for r in search_result[:5]  # Top 5 results
                ]
                
                logger.info(f"  Found {len(search_result)} potential matches")
                
                # Select best match
                if self.matching_agent and search_result:
                    match_selection = await self.matching_agent.select_best_match(
                        line_item, search_result
                    )
                    matches[line_item.line_id] = {
                        "selected_part": match_selection.selected_part_number,
                        "confidence": match_selection.confidence.value if hasattr(match_selection.confidence, 'value') else str(match_selection.confidence),
                        "reasoning": match_selection.reasoning
                    }
                    logger.info(f"  Selected: {match_selection.selected_part_number} (confidence: {match_selection.confidence})")
                else:
                    logger.info("  No suitable match found")
            
            self._save_step_output(session_output_dir, "03_search_results.json", search_results)
            self._save_step_output(session_output_dir, "04_part_matches.json", matches)
            results["steps"]["search_results"] = search_results
            results["steps"]["part_matches"] = matches
            
            # Step 4: Order Assembly
            logger.info("\nSTEP 4: Order Assembly")
            logger.info("-" * 40)
            
            # Convert matches to expected format - create MatchSelection objects
            from app.models.line_item_schemas import MatchSelection, MatchConfidence
            line_item_matches = {}
            for lid, m in matches.items():
                # Convert confidence string back to enum
                confidence_str = m["confidence"]
                if hasattr(MatchConfidence, confidence_str):
                    confidence_enum = getattr(MatchConfidence, confidence_str)
                else:
                    # Try to parse the enum format
                    try:
                        confidence_enum = MatchConfidence(confidence_str.split('.')[-1].lower())
                    except:
                        confidence_enum = MatchConfidence.LOW
                
                line_item_matches[lid] = MatchSelection(
                    selected_part_number=m["selected_part"],
                    confidence=confidence_enum,
                    reasoning=m["reasoning"],
                    match_score=0.5  # Default score
                )
            
            assembled_order = await self.assembly_agent.assemble_order(
                extracted_order, line_item_matches
            )
            
            assembly_output = {
                "order_summary": assembled_order.order_summary,
                "confidence_score": assembled_order.confidence_score,
                "approval_required": assembled_order.approval_required,
                "totals": assembled_order.totals,
                "assembled_line_items": assembled_order.line_items,
                "issues_requiring_review": assembled_order.issues_requiring_review,
                "next_steps": assembled_order.next_steps
            }
            
            self._save_step_output(session_output_dir, "05_assembled_order.json", assembly_output)
            results["steps"]["order_assembly"] = assembly_output
            
            logger.info(f"Order assembled successfully")
            logger.info(f"Confidence Score: {assembled_order.confidence_score}")
            logger.info(f"Approval Required: {assembled_order.approval_required}")
            logger.info(f"Total Items: {assembled_order.totals.get('total_line_items', 0)}")
            logger.info(f"Matched Items: {assembled_order.totals.get('matched_items', 0)}")
            
            # Final summary
            results["end_time"] = datetime.now().isoformat()
            results["status"] = "completed"
            results["summary"] = {
                "total_line_items": len(extracted_order.line_items),
                "successful_matches": len([m for m in matches.values() if m["selected_part"] != "NO_MATCH"]),
                "confidence_score": assembled_order.confidence_score,
                "approval_required": assembled_order.approval_required
            }
            
            self._save_step_output(session_output_dir, "06_final_results.json", results)
            
            logger.info(f"\n{'='*80}")
            logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info(f"All outputs saved to: {session_output_dir}")
            logger.info(f"{'='*80}\n")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            results["error"] = str(e)
            results["status"] = "failed"
            self._save_step_output(session_output_dir, "99_error.json", results)
            raise
    
    def _save_step_output(self, output_dir: Path, filename: str, data: Any):
        """Save step output to file"""
        output_path = output_dir / filename
        
        if isinstance(data, dict) or isinstance(data, list):
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        else:
            with open(output_path, 'w') as f:
                f.write(str(data))
        
        logger.debug(f"Saved output to: {output_path}")

async def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Process sales orders through multi-agent workflow"
    )
    parser.add_argument(
        "file",
        help="Path to the text file containing the order"
    )
    parser.add_argument(
        "--output-dir",
        default="workflow_outputs",
        help="Directory to save workflow outputs (default: workflow_outputs)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize processor
    processor = SimpleWorkflowProcessor(output_dir=args.output_dir)
    
    try:
        # Process the file
        results = await processor.process_file(args.file)
        
        # Print summary
        print(f"\nSUMMARY:")
        print(f"  Session ID: {results['session_id']}")
        print(f"  Status: {results.get('status', 'unknown')}")
        if 'summary' in results:
            print(f"  Total Line Items: {results['summary']['total_line_items']}")
            print(f"  Successful Matches: {results['summary']['successful_matches']}")
            print(f"  Confidence Score: {results['summary']['confidence_score']}")
            print(f"  Approval Required: {results['summary']['approval_required']}")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)