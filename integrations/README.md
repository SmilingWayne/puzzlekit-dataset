# External Integrations

This directory is reserved for pinned upstream tools used by the local
load-solve-write pipeline.

## Naming

We use `integrations/` instead of `third_party/` because these repositories are
not passive copied dependencies. They are active protocol boundaries:

- `pzprjs` provides authoritative puzz.link parsing, normalization, and answer
  checking.
- `noqx` is one possible solver backend for Penpa+ inputs.

## Planned Layout

```text
integrations/
  pzprjs/   # git submodule: robx/pzprjs pinned to a known commit
  noqx/     # git submodule: T0nyX1ang/noqx pinned to a known commit
  tools.json
```

The directories above should be added as git submodules at the tags recorded in
`tools.json`. Submodules are pinned by commit; tags are recorded so humans can
see the upstream release name.

```bash
git submodule add https://github.com/robx/pzprjs.git integrations/pzprjs
git -C integrations/pzprjs checkout v0.12.0
git submodule add https://github.com/T0nyX1ang/noqx.git integrations/noqx
git -C integrations/noqx checkout v0.9.0
git submodule update --init --recursive
```

## Updating Upstreams

When an upstream releases a new tag:

```bash
git -C integrations/pzprjs fetch --tags
git -C integrations/pzprjs checkout <new-pzprjs-tag>

git -C integrations/noqx fetch --tags
git -C integrations/noqx checkout <new-noqx-tag>

pnpm integrations:verify
pnpm test
pnpm typecheck
```

If verification passes, update `tools.json` with the new tag and the checked-out
commit SHA, then commit the manifest and submodule pointer together.

## Replacement Policy

Pipeline code must not call upstream repositories directly. It should go
through adapters in `src/pipeline/`.

That keeps each external tool replaceable:

- Replace `pzprjs` by implementing the same `PzprAdapter` interface.
- Replace `noqx` by registering another `SolverBackend`.

`noqx` is intentionally modeled as a backend, not as the pipeline itself.
