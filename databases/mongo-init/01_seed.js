// ============================================================================
// PyForge Mongo seed — runs on first start of the mongo container.
// Two collections used as ETL *sources* (DocStore, Pipeline Blueprint,
// Airflow Pro) and for document-modeling exercises.
// ============================================================================
db = db.getSiblingDB('appdata');

// Deterministic-ish generator (simple LCG so every learner gets the same data)
let seed = 42;
function rnd() { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; }
function pick(a) { return a[Math.floor(rnd() * a.length)]; }

// -------- product reviews: nested documents, the classic "document" shape
const reviews = [];
for (let i = 1; i <= 800; i++) {
  reviews.push({
    review_id: i,
    product_id: 1 + Math.floor(rnd() * 100),      // joins to warehouse products
    customer_id: 1 + Math.floor(rnd() * 500),
    rating: 1 + Math.floor(rnd() * 5),
    title: pick(['great', 'terrible', 'okay', 'love it', 'broke fast']) + ' #' + i,
    body: 'review body text ' + i,
    helpful_votes: Math.floor(rnd() * 50),
    created_at: new Date(2025, Math.floor(rnd() * 12), 1 + Math.floor(rnd() * 28)),
    aspects: [
      { name: 'quality',  score: 1 + Math.floor(rnd() * 5) },
      { name: 'shipping', score: 1 + Math.floor(rnd() * 5) },
    ],
  });
}
db.reviews.insertMany(reviews);
db.reviews.createIndex({ product_id: 1 });
db.reviews.createIndex({ rating: 1, created_at: -1 });

// -------- clickstream events: the append-only event feed ETL pipelines drain
const events = [];
const types = ['page_view', 'add_to_cart', 'checkout', 'search', 'login'];
for (let i = 1; i <= 3000; i++) {
  events.push({
    event_id: i,
    customer_id: 1 + Math.floor(rnd() * 500),
    type: pick(types),
    url: '/page/' + Math.floor(rnd() * 40),
    ts: new Date(2026, 0, 1 + Math.floor(rnd() * 200), Math.floor(rnd() * 24)),
    meta: { device: pick(['mobile', 'desktop']), session: 's' + Math.floor(rnd() * 900) },
  });
}
db.events.insertMany(events);
db.events.createIndex({ ts: 1 });
db.events.createIndex({ customer_id: 1, ts: -1 });

print('PyForge mongo seed complete: ' +
      db.reviews.countDocuments() + ' reviews, ' +
      db.events.countDocuments() + ' events');
