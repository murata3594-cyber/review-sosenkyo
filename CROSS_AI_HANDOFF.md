# CROSS_AI_HANDOFF.md

Updated: 2026-08-13 JST

## Purpose
This file is the durable handoff between ChatGPT, Codex, Claude/Claude Code, and future agents. Chat history is not the source of truth. The latest GitHub `main` plus the canonical files listed in `AGENTS.md` are the source of truth.

## One-shot startup protocol
When the owner says only something short such as `引き継いで`, `続けて`, `作業再開`, or `このプロジェクトを進めて`, do all of the following without asking the owner to repeat prior chat context:
1. Refresh/read the latest `main`.
2. Read `AGENTS.md` first, then this file, then every file in the `Read first` list in `AGENTS.md`.
3. Inspect the canonical manifests/queues/logs and the current implementation before changing anything.
4. Treat GitHub code/docs as authoritative over stale conversational recollections.
5. Do not duplicate work already implemented by another agent.
6. Continue the highest-priority incomplete safe task autonomously under `AUTONOMOUS_PUBLISHING.md`.
7. Ask the owner only for genuinely external/unavailable actions such as dashboard authentication, approval, domain purchase, or secret entry.
8. Never request or expose secret values that are already stored in Cloudflare or another secret store.

## Current cross-AI state
### Review Sosenkyo
Repository: `murata3594-cyber/review-sosenkyo`
Production: Cloudflare Workers Static Assets.
Current temporary production origin: `https://review-sosenkyo.murata3594.workers.dev`
Planned custom domain: `https://review-sosenkyo.com` (purchase/activation deferred by owner).

Affiliate/monetization state:
- A8.net site registration completed by owner.
- A8 Link Manager tag is stored in Cloudflare Build variables as `A8_LINK_MANAGER_TAG`.
- Build code injects the exact A8-issued tag into production HTML when the variable is present.
- ValueCommerce site registration completed by owner.
- ValueCommerce LinkSwitch tag is stored in Cloudflare Build variables as `VC_LINKSWITCH_TAG`.
- Build code injects the exact LinkSwitch tag when the variable is present.
- PR/affiliate disclosure is injected when affiliate auto-link tooling is enabled.
- Rakuten Web Service integration code exists and the owner has created site/app credentials, but final production URL / allowed-website alignment is intentionally deferred until custom-domain work is resumed. Do not delete the integration.
- Amazon Associates is not yet connected.
- Never commit A8/ValueCommerce tags, Rakuten keys, Amazon tags, or other credentials.

Recent build/QA state:
- Cloudflare build false-positive secret scan against `node_modules/wrangler` was fixed by excluding vendor/build directories while keeping project-source secret scanning strict.
- Site validation reached `PASSED: 24 HTML pages checked; 14 published item(s); 0 warning(s)`.
- Content audit reached PASS; the legacy BRITA research ledger was updated with `raw_review_text_stored=false` to remove the compatibility warning.

Canonical monetization status is maintained in `AFFILIATE_SETUP.md`. If this handoff and `AFFILIATE_SETUP.md` ever conflict, re-check the latest code and update both rather than guessing.

## Counterpart project
The sister site is `murata3594-cyber/military-now-site` (ミリタリーNOW). It uses the same cross-AI operating principle and has its own `AGENTS.md`, `CROSS_AI_HANDOFF.md`, and `AFFILIATE_SETUP.md`.

If the current Codex/workspace has access to both repositories, synchronize decisions that intentionally apply to both sites, but never overwrite project-specific safety rules.

## Default priorities from here
1. Verify successful production injection of A8 Link Manager and ValueCommerce LinkSwitch from build logs/output when accessible.
2. Keep article publishing automation stable; do not let affiliate tooling break builds when a provider is unavailable.
3. Continue relevant A8/ValueCommerce program onboarding only where editorially relevant.
4. Resume Rakuten production activation after the custom domain/allowed website is finalized.
5. Add Amazon Associates only after the owner chooses to proceed and required external registration is complete.
6. Later connect GA4, Search Console, and AdSense through environment-variable gates after the production domain is finalized.

## One sentence the owner should be able to use
`このリポジトリのAGENTS.mdに従い、CROSS_AI_HANDOFF.mdを起点に最新mainから未完了作業を自律的に引き継いで続行して。`
