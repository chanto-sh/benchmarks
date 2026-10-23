package retry

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"
)

func hfake(delays *[]time.Duration) func(context.Context, time.Duration) error {
	return func(ctx context.Context, d time.Duration) error {
		*delays = append(*delays, d)
		return ctx.Err()
	}
}

func TestHiddenLongBackoffStaysCapped(t *testing.T) {
	var delays []time.Duration
	calls := 0
	last := errors.New("still down")
	err := Do(context.Background(), Policy{Attempts: 90, Base: 3 * time.Second, Max: 45 * time.Second, Sleep: hfake(&delays)},
		func() error { calls++; return last })
	if err != last || calls != 90 || len(delays) != 89 {
		t.Fatalf("err=%v calls=%d delays=%d", err, calls, len(delays))
	}
	want := []time.Duration{3 * time.Second, 6 * time.Second, 12 * time.Second, 24 * time.Second, 45 * time.Second}
	for i, d := range delays {
		w := 45 * time.Second
		if i < len(want) {
			w = want[i]
		}
		if d != w {
			t.Fatalf("delay %d = %v, want %v (all: %v)", i, d, w, delays)
		}
	}
}

func TestHiddenHugeBase(t *testing.T) {
	var delays []time.Duration
	Do(context.Background(), Policy{Attempts: 40, Base: time.Hour, Max: 2 * time.Hour, Sleep: hfake(&delays)},
		func() error { return errors.New("x") })
	for i, d := range delays {
		if d <= 0 || d > 2*time.Hour {
			t.Fatalf("delay %d = %v", i, d)
		}
	}
}

func TestHiddenAttemptsBelowOne(t *testing.T) {
	for _, a := range []int{0, -3, 1} {
		calls := 0
		var delays []time.Duration
		e := errors.New("e")
		err := Do(context.Background(), Policy{Attempts: a, Base: time.Millisecond, Max: time.Millisecond, Sleep: hfake(&delays)},
			func() error { calls++; return e })
		if calls != 1 || err != e || len(delays) != 0 {
			t.Fatalf("attempts=%d: calls=%d err=%v delays=%v", a, calls, err, delays)
		}
	}
}

func TestHiddenAlreadyCancelled(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	calls := 0
	err := Do(ctx, Policy{Attempts: 3, Base: time.Millisecond, Max: time.Millisecond}, func() error { calls++; return nil })
	if calls != 0 || !errors.Is(err, context.Canceled) {
		t.Fatalf("calls=%d err=%v", calls, err)
	}
}

func TestHiddenPermanentReturnedAsIs(t *testing.T) {
	inner := errors.New("bad request")
	wrapped := fmt.Errorf("a: %w", fmt.Errorf("b: %w", Permanent(inner)))
	calls := 0
	err := Do(context.Background(), Policy{Attempts: 5, Base: time.Millisecond, Max: time.Millisecond, Sleep: hfake(new([]time.Duration))},
		func() error { calls++; return wrapped })
	if calls != 1 || err != wrapped || !errors.Is(err, inner) {
		t.Fatalf("calls=%d err=%v", calls, err)
	}
	// A non-permanent error after transient ones: last error, exactly.
	n := 0
	errs := []error{errors.New("1"), errors.New("2"), errors.New("3")}
	err = Do(context.Background(), Policy{Attempts: 3, Base: time.Millisecond, Max: time.Millisecond, Sleep: hfake(new([]time.Duration))},
		func() error { n++; return errs[n-1] })
	if err != errs[2] {
		t.Fatalf("got %v", err)
	}
}

func TestHiddenRealSleepCancel(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	go func() { time.Sleep(30 * time.Millisecond); cancel() }()
	start := time.Now()
	calls := 0
	err := Do(ctx, Policy{Attempts: 10, Base: 20 * time.Second, Max: time.Minute}, func() error { calls++; return errors.New("x") })
	if !errors.Is(err, context.Canceled) || calls != 1 || time.Since(start) > 2*time.Second {
		t.Fatalf("err=%v calls=%d took=%v", err, calls, time.Since(start))
	}
}
