package lru

import "testing"

func TestBasic(t *testing.T) {
	c := New(2)
	c.Put("a", 1)
	c.Put("b", 2)
	if v, ok := c.Get("a"); !ok || v != 1 {
		t.Fatal("a")
	}
	c.Put("c", 3) // evicts b
	if _, ok := c.Get("b"); ok {
		t.Fatal("b should be evicted")
	}
	c.Put("a", 10)
	if v, _ := c.Get("a"); v != 10 {
		t.Fatal("update")
	}
	if c.Len() != 2 {
		t.Fatal("len")
	}
}
