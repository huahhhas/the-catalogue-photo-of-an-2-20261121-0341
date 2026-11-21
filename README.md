# THE ZERO-G MUG

[![make.fun](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341)
[![rank](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/huahhhas/the-catalogue-photo-of-an-2-20261121-0341/rank.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341)
[![reward](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/huahhhas/the-catalogue-photo-of-an-2-20261121-0341/reward.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341)

A catalogue photograph of an impossible gadget: **THE ZERO-G MUG** — coffee
that floats, so it can never spill.

`main.py` (Python 3.13, stdlib + Pillow only, runs offline, no network)
draws the shot and writes one 1024x1024 PNG to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`):

- a white ceramic mug on a clean light-grey studio background, soft
  contact shadow, coffee surface visible inside the rim
- a glossy sphere of coffee hovering above the mug, with small droplets
  frozen mid-air between sphere and mug
- exactly one accessory: a single teaspoon floating tilted beside the mug
- product label band reading **ZERO-G / GRAVITY-FREE MUG**
- catalogue caption: "THE ZERO-G MUG — Coffee that floats. Spills that
  don't. — Model ZG-01 · $49.99"

## Run

```sh
python3 main.py
```

Deterministic: the same bytes every run.

## License

MIT — see [LICENSE](LICENSE).
