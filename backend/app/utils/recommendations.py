"""
Recommendation logic for determining which files users should upload based on their website size.
"""
from typing import Literal

RecommendationType = Literal["minimal", "standard", "complete"]


def get_file_recommendation(
    pages_count: int,
    file_size_bytes: int
) -> dict:
    """
    Determine which files to recommend based on website stats.
    
    Args:
        pages_count: Number of pages crawled
        file_size_bytes: Total file size in bytes
        
    Returns:
        dict with recommendation type, title, description, and files list
    """
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    # Determine recommendation type based on requirements
    if pages_count <= 50 and file_size_mb < 2:
        recommendation_type: RecommendationType = "minimal"
    elif pages_count <= 500 and file_size_mb < 10:
        recommendation_type: RecommendationType = "standard"
    else:
        recommendation_type: RecommendationType = "complete"
    
    # Define recommendation details
    recommendations = {
        "minimal": {
            "type": "minimal",
            "title": "Minimal Setup",
            "description": "Your website is small enough to use just the main llms.txt file",
            "files": ["llms.txt"],
            "reason": f"With {pages_count} pages and {file_size_mb:.2f}MB, a single file is sufficient for AI assistants to understand your site."
        },
        "standard": {
            "type": "standard",
            "title": "Standard Setup",
            "description": "Use both llms.txt and llms-full.txt for optimal coverage",
            "files": ["llms.txt", "llms-full.txt"],
            "reason": f"Your site has {pages_count} pages ({file_size_mb:.2f}MB). Using both files provides a good balance of overview and detail."
        },
        "complete": {
            "type": "complete",
            "title": "Complete Setup",
            "description": "Upload the complete folder structure for comprehensive coverage",
            "files": ["llms.txt", "llms-full.txt", "md/ folder (entire structure)"],
            "reason": f"With {pages_count} pages and {file_size_mb:.2f}MB of content, the complete folder structure ensures all content is accessible to AI assistants."
        }
    }
    
    return recommendations[recommendation_type]