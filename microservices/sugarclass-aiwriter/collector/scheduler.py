"""
Automated scheduler for daily news collection.
Uses APScheduler for cron-based scheduling with rate limiting and error recovery.
"""
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import collection modules
from database import init_db, delete_old_articles, log_collection
from collector import collect_from_api
from sources.kids_sources import get_sources_by_age_group
from quality_checker import evaluate_article, should_keep_article
from extraction_pipeline import extract_article
import requests


# Configuration
_RATE_LIMIT_DELAY = 1.0  # Seconds between requests to same domain
_MAX_ARTICLES_PER_SOURCE = 50
_ARTICLES_RETENTION_DAYS = 30
_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0; +https://github.com/yourrepo)"


class NewsCollectionScheduler:
    """Automated news collection scheduler."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.last_collection_times = {}
        init_db()
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            print("[Scheduler] Already running")
            return
        
        # Schedule daily collections by age group
        # 06:00 UTC - Ages 7-10
        self.scheduler.add_job(
            func=lambda: self.collect_age_group("7-10"),
            trigger=CronTrigger(hour=6, minute=0),
            id="collect_7_10",
            name="Collect news for ages 7-10",
            replace_existing=True
        )
        
        # 08:00 UTC - Ages 11-13
        self.scheduler.add_job(
            func=lambda: self.collect_age_group("11-13"),
            trigger=CronTrigger(hour=8, minute=0),
            id="collect_11_13",
            name="Collect news for ages 11-13",
            replace_existing=True
        )
        
        # 10:00 UTC - Ages 14-16
        self.scheduler.add_job(
            func=lambda: self.collect_age_group("14-16"),
            trigger=CronTrigger(hour=10, minute=0),
            id="collect_14_16",
            name="Collect news for ages 14-16",
            replace_existing=True
        )
        
        # 12:00 UTC - Quality check with Gemini
        self.scheduler.add_job(
            func=self.run_quality_checks,
            trigger=CronTrigger(hour=12, minute=0),
            id="quality_check",
            name="Run quality checks on collected articles",
            replace_existing=True
        )
        
        # 14:00 UTC - Cleanup old articles
        self.scheduler.add_job(
            func=self.cleanup_old_articles,
            trigger=CronTrigger(hour=14, minute=0),
            id="cleanup",
            name="Delete articles older than 30 days",
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        print("[Scheduler] Started successfully")
        print("[Scheduler] Jobs scheduled:")
        for job in self.scheduler.get_jobs():
            print(f"  - {job.name} (next run: {job.next_run_time})")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        print("[Scheduler] Stopped")
    
    def collect_age_group(self, age_group: str):
        """
        Collect news for specific age group.
        
        Args:
            age_group: "7-10", "11-13", or "14-16"
        """
        print(f"\n{'='*60}")
        print(f"[Collection] Starting collection for age group: {age_group}")
        print(f"[Collection] Time: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        total_found = 0
        total_stored = 0
        total_rejected = 0
        
        try:
            # Get sources for this age group
            sources = get_sources_by_age_group(age_group)
            
            for source_name, source in sources.items():
                print(f"\n[{source_name}] Fetching articles...")
                
                try:
                    # Fetch articles from source
                    result = source.fetch_articles(limit=_MAX_ARTICLES_PER_SOURCE)
                    
                    if result.articles_found == 0:
                        print(f"[{source_name}] No articles found")
                        continue
                    
                    print(f"[{source_name}] Found {result.articles_found} articles")
                    total_found += result.articles_found
                    
                    # Process each article
                    for article_data in getattr(result, 'articles', []):
                        # Rate limiting
                        time.sleep(_RATE_LIMIT_DELAY)
                        
                        # Extract full article if needed
                        if not article_data.full_text:
                            success = self._extract_full_article(article_data)
                            if not success:
                                print(f"[{source_name}] Failed to extract: {article_data.url}")
                                total_rejected += 1
                                continue
                        
                        # Quality check
                        evaluation = evaluate_article(
                            article_data.title,
                            article_data.full_text,
                            use_gemini=False  # Don't use Gemini during collection (too slow)
                        )
                        
                        # Check if we should keep this article
                        if not should_keep_article(evaluation):
                            print(f"[{source_name}] Rejected (quality): {article_data.title[:50]}...")
                            total_rejected += 1
                            continue
                        
                        # Update article with quality metrics
                        article_data.age_group = evaluation.get('age_group')
                        article_data.readability_score = evaluation.get('readability_score')
                        article_data.grade_level = evaluation.get('grade_level')
                        article_data.word_count = evaluation.get('word_count')
                        
                        # Store article
                        # TODO: Integrate with database.insert_article()
                        total_stored += 1
                        print(f"[{source_name}] ✓ Stored: {article_data.title[:50]}...")
                    
                    # Log collection for this source
                    duration = (datetime.now() - start_time).total_seconds()
                    log_collection(
                        source=source_name,
                        articles_found=result.articles_found,
                        articles_stored=total_stored,
                        articles_failed=total_rejected,
                        started_at=start_time.isoformat(),
                        completed_at=datetime.now().isoformat(),
                        error_message=None
                    )
                
                except Exception as e:
                    print(f"[{source_name}] Error: {e}")
                    log_collection(
                        source=source_name,
                        articles_found=0,
                        articles_stored=0,
                        articles_failed=0,
                        started_at=start_time.isoformat(),
                        completed_at=datetime.now().isoformat(),
                        error_message=str(e)
                    )
            
            # Summary
            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n{'='*60}")
            print(f"[Collection] Completed for age group: {age_group}")
            print(f"[Collection] Duration: {duration:.1f}s")
            print(f"[Collection] Found: {total_found}, Stored: {total_stored}, Rejected: {total_rejected}")
            print(f"{'='*60}\n")
        
        except Exception as e:
            print(f"[Collection] Fatal error: {e}")
    
    def _extract_full_article(self, article_data) -> bool:
        """
        Extract full article content from URL.
        
        Args:
            article_data: Article object to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch HTML
            response = requests.get(
                article_data.url,
                headers={'User-Agent': _USER_AGENT},
                timeout=10
            )
            response.raise_for_status()
            
            # Extract using pipeline
            title, text, method, metadata = extract_article(response.text, article_data.url)
            
            if text and len(text) > 100:
                article_data.full_text = text
                article_data.extraction_method = method
                
                # Update title if extracted one is better
                if title and not article_data.title:
                    article_data.title = title
                
                return True
            
            return False
        
        except Exception as e:
            print(f"[Extraction] Error: {e}")
            return False
    
    def run_quality_checks(self):
        """Run Gemini quality checks on pending articles."""
        print("\n[QualityCheck] Starting Gemini quality review...")
        
        # TODO: Implement batch quality checking with Gemini API
        # This would:
        # 1. Query articles with quality_check_status='pending'
        # 2. Send to Gemini for evaluation (batch of 10-20 at a time)
        # 3. Update quality_score and quality_check_status
        # 4. Remove articles with score < 5
        
        print("[QualityCheck] Not yet implemented - placeholder")
    
    def cleanup_old_articles(self):
        """Delete articles older than retention period."""
        print(f"\n[Cleanup] Deleting articles older than {_ARTICLES_RETENTION_DAYS} days...")
        
        try:
            deleted = delete_old_articles(days=_ARTICLES_RETENTION_DAYS)
            print(f"[Cleanup] Deleted {deleted} old articles")
        
        except Exception as e:
            print(f"[Cleanup] Error: {e}")
    
    def run_manual_collection(self, age_group: Optional[str] = None):
        """
        Manually trigger collection (for testing).
        
        Args:
            age_group: Optional specific age group, or all if None
        """
        if age_group:
            self.collect_age_group(age_group)
        else:
            for ag in ["7-10", "11-13", "14-16"]:
                self.collect_age_group(ag)


# Global scheduler instance
_scheduler = None


def start_scheduler():
    """Start the global scheduler."""
    global _scheduler
    
    if _scheduler is None:
        _scheduler = NewsCollectionScheduler()
    
    _scheduler.start()
    return _scheduler


def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()


def get_scheduler() -> Optional[NewsCollectionScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


# CLI for manual testing
if __name__ == "__main__":
    import sys
    
    print("NewsCollect Scheduler")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "collect":
            # Manual collection
            age_group = sys.argv[2] if len(sys.argv) > 2 else None
            scheduler = NewsCollectionScheduler()
            scheduler.run_manual_collection(age_group)
        
        elif command == "start":
            # Start daemon
            scheduler = start_scheduler()
            print("\nScheduler running. Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping scheduler...")
                stop_scheduler()
        
        else:
            print(f"Unknown command: {command}")
            print("Usage:")
            print("  python scheduler.py collect [age_group]  - Manual collection")
            print("  python scheduler.py start                - Start scheduler daemon")
    
    else:
        print("Usage:")
        print("  python scheduler.py collect [age_group]  - Manual collection")
        print("  python scheduler.py start                - Start scheduler daemon")
        print("\nAge groups: 7-10, 11-13, 14-16")
