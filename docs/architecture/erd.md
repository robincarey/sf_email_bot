# Canonical Data Model ERD

This ERD documents the normalized catalog layer used to map raw scrape records to
stable entities for product features and analytics.

```mermaid
erDiagram
    publishers ||--o{ collections : has
    publishers ||--o{ editions : publishes
    works ||--o{ editions : has
    collections ||--o{ retailer_listings : contains
    editions ||--o{ retailer_listings : listedAs
    items_seen ||--o{ retailer_listings : lineage

    publishers {
      int id PK
      string name
      string country
      string base_url
      boolean active
      datetime created_at
    }

    collections {
      int id PK
      int publisher_id FK
      string name
      string store_name
      string scrape_url
      boolean active
      datetime created_at
    }

    works {
      int id PK
      string title
      string author
      string normalized_title
      string normalized_author
      string open_library_id
      datetime created_at
    }

    editions {
      int id PK
      int work_id FK
      int publisher_id FK
      string title
      string normalized_title
      string isbn
      string edition_type
      int print_run_size
      string physical_format
      datetime created_at
    }

    retailer_listings {
      int id PK
      int edition_id FK
      int collection_id FK
      bigint items_seen_id FK
      string retailer_url
      string retailer_url_normalized
      boolean in_stock
      int price_cents
      datetime last_checked
      datetime created_at
    }

    items_seen {
      bigint id PK
      string name
      string store
      string link
      boolean in_stock
      int typed_price_cents
      datetime last_checked
    }
```

## Contract highlights

- `works` uniqueness: `(normalized_title, coalesce(normalized_author, ''))`
- `editions` uniqueness: `(work_id, publisher_id, normalized_title, coalesce(edition_type, ''))`
- `retailer_listings` uniqueness: `(collection_id, retailer_url_normalized)`
- `collections.store_name` is the compatibility bridge to existing preference logic

## Rendering fallback

Some markdown preview renderers (including certain IDE preview modes) do not execute
Mermaid blocks. Keep this Mermaid source as the canonical editable diagram and commit
a static export for universal visibility.

Recommended static artifact path:

- `docs/architecture/erd.png`

Optional markdown image embed once exported:

```md
![Canonical Data Model ERD](./erd.png)
```

