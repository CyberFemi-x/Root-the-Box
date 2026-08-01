# Rabbit-Hole Analysis

## Candidate edge: Direct sudo escalation via the injected web-shell process

### Precondition (as it appeared)

Enumeration of the `support` account's sudo permissions returned a
seemingly complete, valid escalation path:

```
User support may run the following commands on nf-eh-a2-vulnerable:
    (root) NOPASSWD: /usr/local/sbin/support-backup
```

This is a genuinely correct sudoers entry — `support` really can run
`/usr/local/sbin/support-backup` as root with no password required. On
its face, this satisfies every normal precondition for a standard sudo
privilege-escalation path: the binary exists, the rule is unconditional
(`NOPASSWD`), and the calling user matches. A naive or time-pressured
attempt would reasonably assume this is directly usable from the
existing command-injection foothold.

### Action attempted

From the command-injection foothold (via `/diagnose`, running as
`support` inside the `netforge-support` systemd service process), the
following was attempted:

```
sudo -l
sudo /usr/local/sbin/support-backup
```

### Expected result (if the precondition genuinely held)

`sudo` should have listed and then permitted execution of
`/usr/local/sbin/support-backup` as root, providing an immediate,
trivial path to root access without needing any further chain steps.

### Actual (failure) result

`sudo` refused to elevate, reporting that the `NoNewPrivileges` systemd
sandboxing directive set on the `netforge-support.service` unit
prevents any process within that service's process tree from gaining
new privileges via `sudo`, `setuid`, or similar mechanisms — regardless
of what the sudoers file itself allows.

This is the actual hidden precondition: **not** "does `support` have a
valid sudo rule" (true), but "is the calling process tree permitted to
use it" (false, for anything spawned by `netforge-support.service`).
The sudoers entry visible in `sudo -l` is real bait: correct, verifiable,
and exactly what a real escalation path looks like — but unusable from
this specific foothold.

### Rejection test / how this was distinguished from a real edge

The distinguishing test was straightforward: attempt the sudo call
directly from the existing foothold and observe the specific systemd
`NoNewPrivileges` denial message, rather than a generic "permission
denied" or sudoers-parsing error. This confirms the sudoers rule itself
is not the blocker — the process's execution context is. This is a
structurally different failure from "the sudo rule doesn't apply to
you," and recognizing the distinction is what correctly rules out
brute-forcing this path further (e.g., repeated sudo attempts, trying
alternate injection payloads) in favor of finding a different execution
context.

### How the real path was found instead

Since the restriction is scoped to the specific process tree of
`netforge-support.service`, not to the `support` user in general, a
fresh, independent process tree (a normal interactive login) is not
subject to the same sandboxing. An SSH keypair was injected into
`support`'s `authorized_keys` via the same command-injection foothold,
and a direct SSH session was established. From that session, `sudo -l`
and `sudo /usr/local/sbin/support-backup` behaved as the sudoers entry
actually promised, confirming this was the correct precondition:
process execution context, not sudoers configuration.

### Cleanup obligation

No artifacts are created by attempting `sudo -l` / `sudo
/usr/local/sbin/support-backup` from the injection point itself (the
attempt fails before any state is modified) — no cleanup action is
required for this rejected edge specifically. Artifacts from the
subsequent successful SSH-based path (injected key, uploaded
checkpoint files, hook script) are cleaned up separately as part of the
main chain's `cleanup_target()` step; see reliability.json and
cleanup-results.xml.