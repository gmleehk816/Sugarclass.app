# Changelog

All notable changes to the News Collector project.

---

## [1.0.0] - 2025-01-10

### 🎉 Initial Release

**Major Features:**
- 3-column responsive layout (left sidebar, main content, right sidebar)
- Age-based filtering (7-10, 11-13, 14-16, 17+)
- 57 RSS sources configured across 12 categories
- Multi-method article extraction (trafilatura → newspaper4k → HTML parser)
- RESTful JSON API for all data operations
- SQLite database with 228 classified articles

---

## Development History

### Phase 1: Foundation (2025-01-08 to 2025-01-10)

#### 2025-01-10
**Added:**
- 3-column CSS Grid layout implementation
- Purple gradient left sidebar with age buttons
- White middle content area with article grid
- White right sidebar with statistics and filters
- Comprehensive documentation structure:
  - README.md (project overview)
  - docs/API.md (endpoint reference)
  - docs/SETUP.md (installation guide)
  - docs/CATEGORIES.md (category taxonomy)
  - docs/SOURCES.md (source directory)
  - docs/ARCHITECTURE.md (system design)
  - docs/DEVELOPMENT.md (contribution guide)
  - docs/CHANGELOG.md (this file)

**Changed:**
- Port changed from 5002 to 7000 (to avoid conflicts)
- Age button layout from horizontal grid to vertical stack
- Body layout from centered container to full-screen grid
- Updated run_server.py for port 7000

**Fixed:**
- Server crash loop on port 5002
- Port conflict with other Flask applications

#### 2025-01-09
**Added:**
- Age group button-based filtering (replaced dropdown)
- 21 new diverse sources:
  - General News: Guardian (2 feeds), NPR (2 feeds), Al Jazeera
  - Entertainment: Polygon, IGN, Pitchfork, Variety
  - Sports: ESPN (2 feeds), Bleacher Report
  - Education: Inside Higher Ed, EdSurge, Edutopia
  - Arts: Artnet, Hyperallergic
  - Social Issues: ProPublica, Vox, The Intercept
  - Tech: TechCrunch, The Verge
- classify_existing.py script for bulk age classification
- delete_paywalled.py script for cleanup

**Changed:**
- Extraction order: trafilatura first, then newspaper4k, then html_parser
- Source count: 36 → 57 sources

**Fixed:**
- Articles lacking age_group data (classified 238 articles)
- Wired article extraction failing (trafilatura works, newspaper4k fails on brotli compression)

**Removed:**
- 10 paywalled articles (Economist, HBR, Atlantic, Rolling Stone)

#### 2025-01-08
**Added:**
- app_enhanced.py (Flask web application)
- database.py (SQLite operations)
- simple_collector.py (RSS collector with 36 sources)
- run_server.py (auto-restart server manager)
- smart_classifier.py (LLM-based age classification)
- Initial 36 sources:
  - 11 general news sources
  - 13 science & tech sources
  - 5 entertainment sources
  - 3 education sources
  - 2 sports sources
  - 2 arts sources

**Database Schema:**
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_date TEXT,
    description TEXT,
    full_text TEXT,
    image_url TEXT,
    categories TEXT,
    age_group TEXT,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source ON articles(source_name);
CREATE INDEX idx_date ON articles(published_date);
CREATE INDEX idx_age_group ON articles(age_group);
```

---

## Statistics Snapshot (2025-01-10)

### Articles
- **Total**: 228 articles
- **Full Text**: ~184 articles (81%)
- **With Images**: ~150 articles (66%)
- **Age Distribution**:
  - 7-10 years: 20 articles (9%)
  - 11-13 years: 38 articles (17%)
  - 14-16 years: 120 articles (53%)
  - 17+ years: 60 articles (26%)
  - Unclassified: 0 articles (0%)

### Sources
- **Configured**: 57 sources
- **Collected**: 11 sources (19%)
- **Categories**: 12 categories
- **Paywalled Removed**: 4 sources

### Coverage by Category
| Category | Sources | Articles | Status |
|----------|---------|----------|--------|
| General News | 5 | 45 | ⭐⭐⭐⭐ Good |
| Science & Technology | 6 | 78 | ⭐⭐⭐⭐⭐ Excellent |
| Health & Medicine | 0 | 0 | ❌ None |
| Arts & Culture | 2 | 18 | ⭐⭐ Poor |
| Entertainment | 4 | 32 | ⭐⭐⭐ Fair |
| Sports | 2 | 15 | ⭐⭐ Poor |
| Business & Economics | 0 | 0 | ❌ None |
| Education | 3 | 25 | ⭐⭐⭐ Fair |
| Lifestyle | 0 | 0 | ❌ None |
| Social Issues | 2 | 10 | ⭐ Very Poor |
| History & Geography | 3 | 5 | ⭐ Very Poor |
| Nature & Environment | 3 | 0 | ❌ None |

---

## Roadmap

### Phase 2 (In Progress)
**Goal**: Content Expansion and Collection

**Planned Features:**
- [ ] Collect from remaining 46 sources
- [ ] Populate categories sidebar with JavaScript
- [ ] Apply LLM classification to existing 228 articles
- [ ] Remove paywalled sources from simple_collector.py code
- [ ] Add 20+ more diverse sources (target: 75-80 total)
- [ ] Improve category coverage (aim for 20+ articles per category)

**Priority Categories to Fill:**
1. Health & Medicine (0 articles) - Add Mayo Clinic, WebMD, Healthline
2. Business & Economics (0 articles) - Add Forbes, TechCrunch, Entrepreneur
3. Lifestyle (0 articles) - Add Teen Vogue, Bon Appétit
4. Nature & Environment (0 articles) - Collect from configured sources

**Estimated Timeline**: 2-3 weeks

### Phase 3 (Future)
**Goal**: Enhanced Features and User Experience

**Planned Features:**
- [ ] Category sidebar with clickable filters
- [ ] Source filter dropdown
- [ ] Multi-select filtering (age + category + source)
- [ ] Article bookmarking/favorites
- [ ] Reading progress tracking
- [ ] Dark mode toggle
- [ ] Print-friendly article view
- [ ] Share article functionality

**Estimated Timeline**: 1-2 months

### Phase 4 (Future)
**Goal**: Advanced Features and Automation

**Planned Features:**
- [ ] Scheduled automatic collection (daily cron job)
- [ ] LLM-powered content summarization
- [ ] Reading comprehension difficulty scoring
- [ ] Recommended articles based on age/interests
- [ ] Multi-language support (Spanish, French)
- [ ] User accounts and preferences
- [ ] Article rating/feedback system
- [ ] Related articles suggestions

**Estimated Timeline**: 2-3 months

---

## Known Issues

### Current Bugs
- None reported

### Limitations
1. **Port 7000 Only**: No auto-detection of available ports
2. **Manual Collection**: No scheduled automatic article collection
3. **Single-Language**: English only (no multi-language support)
4. **No Pagination**: All articles load at once (may slow with 1000+ articles)
5. **Static Categories**: Categories not clickable/filterable yet
6. **LLM Classification**: Not applied to existing 228 articles
7. **Paywalled Sources**: Still in code, just not collected from

### Technical Debt
1. **Duplicate Code**: HTML/CSS embedded in app_enhanced.py (should be in templates/)
2. **No Tests**: No automated unit/integration tests
3. **No CI/CD**: Manual deployment process
4. **SQLite Limits**: Will need PostgreSQL for >10,000 articles
5. **No Caching**: API responses not cached
6. **No Rate Limiting**: API has no request limits

---

## Migration Notes

### Upgrading from 0.x to 1.0

**Database Migration Required**: No (new project)

**Configuration Changes**:
- Port changed: 5002 → 7000
- New environment variable: `LLM_MODEL=gemini-2.5-flash`

**Breaking Changes**: None (first release)

---

## Contributors

- Primary Developer: [Your Name]
- Documentation: [Your Name]
- Testing: [Your Name]

---

## Version Scheme

This project follows [Semantic Versioning](https://semver.org/):

**Format**: MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes (database schema, API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

**Examples**:
- 1.0.0 → 1.0.1: Bug fix (extraction error fixed)
- 1.0.0 → 1.1.0: New feature (category sidebar added)
- 1.0.0 → 2.0.0: Breaking change (API endpoint renamed)

---

## Release Process

1. Update version in README.md
2. Update CHANGELOG.md with new version section
3. Test all functionality
4. Backup database
5. Commit changes: `git commit -m "Release v1.0.0"`
6. Tag release: `git tag v1.0.0`
7. Push: `git push origin main --tags`
8. Deploy to production

---

## Contact

For questions or issues, contact: [Your Email]

Project Repository: [GitHub URL if applicable]

---

**Last Updated**: 2025-01-10
