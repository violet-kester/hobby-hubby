# Forums App

Forum system with categories, threads, posts, voting, bookmarks, and search.

## Models

### Hierarchy: Category > Subcategory > Thread > Post

**Category**
- Fields: name, slug (auto), color_theme, icon, order
- 6 fixed hobby categories with color themes

**Subcategory**
- Fields: category (FK), name, slug, description, member_count
- Unique: (category, name), (category, slug)

**Thread**
- Fields: subcategory (FK), author (FK), title, slug, is_pinned, is_locked, view_count, post_count, last_post_at
- Ordered: -is_pinned, -last_post_at

**Post**
- Fields: thread (FK), author (FK), content, is_edited, edited_at, vote_count
- Signals update thread.post_count and last_post_at

**PostImage**
- Fields: post (FK), image, caption, order
- Storage: `post_images/%Y/%m/`
- Validation: jpg/png/gif/webp, 10MB max

### Interactions

**Vote**: user + post (unique), updates post.vote_count via signals
**Bookmark**: user + thread (unique)

### Search Models

**SearchHistory**
- Fields: user, query, content_type, results_count
- `record_search()`: Creates with 1-hour duplicate prevention
- `get_user_recent_searches(limit)`, `get_popular_searches(limit)`

**SavedSearch**
- Fields: user, name (unique per user), query, content_type, sort_by, is_active, last_used_at
- `get_search_url()`: Generates URL with encoded params

**SearchAnalytics**
- Tracks: search_time_ms, database_hits, clicked_result_position, user_agent, ip_address (anonymized)
- `record_search_analytics()`, `record_result_click()`, `get_search_trends()`, `get_performance_metrics()`

## Views

### Browsing (Class-Based)
| View | URL | Notes |
|------|-----|-------|
| CategoryListView | `/forums/` | Lists all categories |
| SubcategoryDetailView | `/forums/<cat>/<subcat>/` | Threads, 20/page |
| ThreadDetailView | `/forums/<cat>/<subcat>/<thread>/` | Posts, 10/page, increments view_count |

### Content Creation (@login_required)
| View | URL | Notes |
|------|-----|-------|
| thread_create | `/forums/<cat>/<subcat>/new/` | Up to 5 images |
| post_create | `/forums/<cat>/<subcat>/<thread>/reply/` | Checks is_locked |
| vote_post | `/forums/vote/<post_id>/` | AJAX, prevents self-vote |
| bookmark_thread | `/forums/bookmark/<thread_id>/` | AJAX toggle |

### Search
| View | URL | Notes |
|------|-----|-------|
| search_view | `/forums/search/` | Dual PostgreSQL/SQLite support |
| search_suggestions_view | `/forums/search/suggestions/` | AJAX, max 8 results |
| save_search_view | `/forums/search/save/` | AJAX POST |
| saved_searches_view | `/forums/search/saved/` | List saved |
| search_history_view | `/forums/search/history/` | Date-grouped |

### API (JSON)
| Endpoint | URL | Notes |
|----------|-----|-------|
| api_search | `/forums/api/search/` | GET/POST, pagination |
| api_search_suggestions | `/forums/api/search/suggestions/` | Mobile autocomplete |
| api_search_analytics | `/forums/api/search/analytics/` | Staff only |

## Forms

| Form | Key Validation |
|------|----------------|
| ThreadCreateForm | title (200), content (10000), bleach sanitization |
| PostCreateForm | content (10000), bleach sanitization |
| SearchForm | query (2-200 chars), strip_tags, date range validation |
| PostImageForm | 10MB, content-type whitelist |

Allowed HTML tags: b, strong, i, em, u, br, p

## Template Tags

`{% load search_tags %}`

| Tag/Filter | Usage |
|------------|-------|
| `highlight_search_terms` | `{{ text\|highlight_search_terms:query }}` |
| `search_result_snippet` | `{% search_result_snippet content query 200 %}` |
| `highlight_in_suggestions` | For autocomplete |
| `truncate_and_highlight` | `{{ text\|truncate_and_highlight:"100,query" }}` |

## Security

- Content sanitized with bleach (whitelist tags)
- Search queries: min 2 chars, max 200, strip_tags
- File uploads: 10MB, whitelist validation
- AJAX endpoints validate X-Requested-With header
- Self-voting prevented by unique constraint
- Thread locking enforced in post_create
- IP addresses anonymized in analytics
- API analytics endpoint staff-only

## Performance

- `select_related()` / `prefetch_related()` for efficient queries
- Denormalized counts via Django signals (post_count, vote_count)
- `F()` expressions for atomic view_count increment
- Database indexes on filtered fields
- Pagination: 20 threads, 10 posts, 20 search results
