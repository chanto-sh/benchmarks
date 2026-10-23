// Package retry retries flaky operations with capped exponential backoff.
package retry

import (
	"context"
	"errors"
	"time"
)

// Policy configures Do.
type Policy struct {
	Attempts int           // total calls of fn (values below 1 mean 1)
	Base     time.Duration // delay before the 2nd call; doubles before each later call
	Max      time.Duration // no single delay is ever longer than this
	// Sleep waits for d or until ctx is done (returning ctx.Err() then).
	// Nil means a real sleep. Tests inject a fake.
	Sleep func(ctx context.Context, d time.Duration) error
}

type permanent struct{ err error }

func (p *permanent) Error() string { return p.err.Error() }
func (p *permanent) Unwrap() error { return p.err }

// Permanent marks err as not worth retrying. It may be wrapped further
// (fmt.Errorf("...: %w", retry.Permanent(err))) and is still recognized.
func Permanent(err error) error { return &permanent{err} }

func defaultSleep(ctx context.Context, d time.Duration) error {
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-t.C:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func backoff(p Policy, n int) time.Duration {
	d := p.Base << uint(n-1)
	if d > p.Max {
		d = p.Max
	}
	return d
}

// Do calls fn until it returns nil, returns a permanent error, the attempts
// run out, or ctx is done. The delay before call n+1 is Base*2^(n-1), capped
// at Max. It returns nil on success, ctx.Err() if ctx ends first (fn is not
// called at all if ctx is already done), and otherwise the last error fn
// returned, exactly as fn returned it.
func Do(ctx context.Context, p Policy, fn func() error) error {
	sleep := p.Sleep
	if sleep == nil {
		sleep = defaultSleep
	}
	attempts := p.Attempts
	if attempts < 1 {
		attempts = 1
	}
	var err error
	for n := 1; n <= attempts; n++ {
		if cerr := ctx.Err(); cerr != nil {
			return cerr
		}
		err = fn()
		if err == nil {
			return nil
		}
		var perm *permanent
		if errors.As(err, &perm) {
			return err
		}
		if n == attempts {
			break
		}
		if serr := sleep(ctx, backoff(p, n)); serr != nil {
			return serr
		}
	}
	return err
}
