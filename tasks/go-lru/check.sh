#!/bin/bash
cat > hidden_test.go <<'GO'
package lru

import "testing"

func TestHiddenEviction(t *testing.T) {
	c := New(3)
	for i, k := range []string{"a", "b", "c"} {
		c.Put(k, i)
	}
	c.Get("a")
	c.Put("d", 4) // evicts b (LRU)
	if _, ok := c.Get("b"); ok {
		t.Fatal("b should be evicted")
	}
	for _, k := range []string{"a", "c", "d"} {
		if _, ok := c.Get(k); !ok {
			t.Fatal("missing " + k)
		}
	}
	c.Put("c", 30) // update moves c to front
	c.Put("e", 5)  // evicts a
	if _, ok := c.Get("a"); ok {
		t.Fatal("a should be evicted")
	}
	if c.Len() != 3 {
		t.Fatal("len")
	}
	one := New(1)
	one.Put("x", 1)
	one.Put("y", 2)
	if _, ok := one.Get("x"); ok || one.Len() != 1 {
		t.Fatal("cap 1")
	}
}
GO
go test ./... 2>&1; r=$?; rm -f hidden_test.go; exit $r
