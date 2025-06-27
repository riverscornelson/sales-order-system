from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


class MatchProcessor:
    """Handles match deduplication, scoring, and explanation generation"""
    
    def __init__(self, max_matches_per_item: int = 5):
        self.max_matches_per_item = max_matches_per_item
    
    def deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate matches by part ID, keeping the highest scoring version"""
        if not matches:
            return []
        
        # Group by part ID
        matches_by_id = {}
        for match in matches:
            part_id = match.get("part", {}).get("id")
            if not part_id:
                continue
            
            current_score = match.get("scores", {}).get("strategy_weighted_score", 0)
            
            if part_id not in matches_by_id:
                matches_by_id[part_id] = match
            else:
                existing_score = matches_by_id[part_id].get("scores", {}).get("strategy_weighted_score", 0)
                if current_score > existing_score:
                    matches_by_id[part_id] = match
        
        return list(matches_by_id.values())
    
    def sort_and_limit_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort matches by score and limit to configured maximum"""
        if not matches:
            return []
        
        # Sort by weighted score
        sorted_matches = sorted(
            matches,
            key=lambda x: x.get("scores", {}).get("strategy_weighted_score", 0),
            reverse=True
        )
        
        return sorted_matches[:self.max_matches_per_item]
    
    def generate_match_explanation(self, item: Dict[str, Any], match: Dict[str, Any]) -> str:
        """Generate a human-readable explanation for why this match was selected"""
        part = match.get("part", {})
        scores = match.get("scores", {})
        strategy = match.get("search_strategy", "unknown")
        
        explanation_parts = []
        
        # Strategy explanation
        strategy_explanations = {
            "PartNumberStrategy": "Matched by part number",
            "FullDescriptionStrategy": "Matched by description",
            "NormalizedDescriptionStrategy": "Matched by normalized description",
            "KeyTermsStrategy": "Matched by key terms",
            "FuzzyMatchStrategy": "Fuzzy match on partial terms"
        }
        explanation_parts.append(strategy_explanations.get(strategy, f"Matched using {strategy}"))
        
        # Score explanation
        combined_score = scores.get("combined_score", 0)
        if combined_score >= 0.9:
            explanation_parts.append("Very high confidence match")
        elif combined_score >= 0.7:
            explanation_parts.append("High confidence match")
        elif combined_score >= 0.5:
            explanation_parts.append("Moderate confidence match")
        else:
            explanation_parts.append("Low confidence match")
        
        # Material match
        if item.get("material") and part.get("material"):
            if item["material"].lower() in part["material"].lower():
                explanation_parts.append("Material matches request")
        
        # Dimension match
        if scores.get("dimension_match"):
            explanation_parts.append("Dimensions match specifications")
        
        return " - ".join(explanation_parts)
    
    def calculate_match_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall quality metrics for a set of matches"""
        if not matches:
            return {
                "average_confidence": 0,
                "best_confidence": 0,
                "match_quality": "no_match"
            }
        
        scores = [m.get("scores", {}).get("strategy_weighted_score", 0) for m in matches]
        avg_score = sum(scores) / len(scores)
        best_score = max(scores)
        
        if best_score >= 0.8:
            quality = "excellent"
        elif best_score >= 0.6:
            quality = "good"
        elif best_score >= 0.4:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "average_confidence": avg_score,
            "best_confidence": best_score,
            "match_quality": quality
        }