package retry

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"
)

func fake(delays *[]time.Duration) func(context.Context, time.Duration) error {
	return func(ctx context.Context, d time.Duration) error {
		*delays = append(*delays, d)
		return ctx.Err()
	}
}

func TestSucceedsAfterFailures(t *testing.T) {
	var delays []time.Duration
	calls := 0
	err := Do(context.Background(), Policy{Attempts: 5, Base: 100 * time.Millisecond, Max: time.Second, Sleep: fake(&delays)},
		func() error {
			calls++
			if calls < 3 {
				return errors.New("flaky")
			}
			return nil
		})
	if err != nil || calls != 3 {
		t.Fatalf("err=%v calls=%d", err, calls)
	}
	if fmt.Sprint(delays) != "[100ms 200ms]" {
		t.Fatalf("delays %v", delays)
	}
}

func TestWrappedPermanentStops(t *testing.T) {
	calls := 0
	base := errors.New("404")
	var delays []time.Duration
	err := Do(context.Background(), Policy{Attempts: 4, Base: time.Millisecond, Max: time.Second, Sleep: fake(&delays)},
		func() error {
			calls++
			return fmt.Errorf("get /x: %w", Permanent(base))
		})
	if calls != 1 || !errors.Is(err, base) {
		t.Fatalf("calls=%d err=%v", calls, err)
	}
}

func TestCancelDuringBackoff(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	start := time.Now()
	err := Do(ctx, Policy{Attempts: 3, Base: 5 * time.Second, Max: time.Minute}, func() error { return errors.New("down") })
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("err=%v", err)
	}
	if time.Since(start) > time.Second {
		t.Fatalf("Do ignored the context for %v", time.Since(start))
	}
}
