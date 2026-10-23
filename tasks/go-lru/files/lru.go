package lru

// Cache is a fixed-capacity least-recently-used cache.
type Cache struct {
	capacity int
}

// New creates a cache holding at most capacity entries (capacity >= 1).
func New(capacity int) *Cache {
	return &Cache{capacity: capacity}
}

// Get returns the value for key and whether it was present.
func (c *Cache) Get(key string) (int, bool) {
	panic("not implemented")
}

// Put inserts or updates key.
func (c *Cache) Put(key string, value int) {
	panic("not implemented")
}

// Len returns the number of entries.
func (c *Cache) Len() int {
	panic("not implemented")
}
