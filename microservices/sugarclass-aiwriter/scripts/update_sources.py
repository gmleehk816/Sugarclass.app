from backend.database import get_db, init_db

def update_sources():
    # Run init_db first to add any new sources
    init_db()
    
    # Manually update URLs for old ones
    updates = [
        ("cnn.com", "https://rss.cnn.com/rss/edition.rss"),
        ("bbc.com", "https://feeds.bbci.co.uk/news/rss.xml"),
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        for domain, url in updates:
            cursor.execute("UPDATE sources SET rss_url = %s WHERE domain = %s" if hasattr(cursor, 'mogrify') else "UPDATE sources SET rss_url = ? WHERE domain = ?", (url, domain))
        conn.commit()
    print("Default sources updated successfully.")

if __name__ == "__main__":
    update_sources()
