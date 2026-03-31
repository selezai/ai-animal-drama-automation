# South African Earning App Research & Feasibility Analysis

**Date:** March 24, 2026  
**Status:** Research Complete — On Hold (Capital Required)

---

## Executive Summary

### The Concept
A mobile app/webapp that allows South Africans to earn R50+/week through:
- Passive income (ads, data sharing, bandwidth)
- Gamification (play/compete for rewards)
- Micro-tasks (surveys, AI training, offerwalls)

**Business model:** Platform takes a 25-35% cut of all earnings.

### The Verdict
**Technically feasible, but requires R30-100k working capital** to bridge the gap between user payouts and network payments. Without capital, this cannot launch.

---

## Market Research Findings

### South African Context
- **Unemployment rate:** ~32% official, ~42% expanded (~8 million people)
- **Smartphone users:** ~24 million
- **Minimum wage:** R28.79/hour (2025)
- **R50/week = ~1.7 hours of minimum wage work**

### Existing Earning Apps in SA (Competitors)

| App | Earnings | Type | Problems |
|-----|----------|------|----------|
| Upwork/Fiverr | R3k-50k/month | Skilled freelance | Requires skills |
| Prolific | R500-2k/month | Academic surveys | Limited availability |
| Remotasks | R300-1,500/week | AI training tasks | Requires training |
| Swagbucks | R300-800/month | Surveys + shopping | Low payouts |
| Clickworker/UHRS | R54-126/hour | Micro-tasks | Complex onboarding |
| Pawns.app | R50-150/month | Bandwidth sharing | Very low earnings |
| MOBROG | R300-1,200/month | Surveys | Limited surveys |

**Key insight:** Apps paying R50+/week require active skilled work, not passive use.

### Why Existing Apps Are "Hard"
1. Low task availability
2. High payout thresholds (R150-500 minimum)
3. Survey disqualification after wasting time
4. Delayed payments (7-30 days)
5. Geographic restrictions (best tasks unavailable in SA)
6. Declining earnings over time

---

## Revenue Model Analysis

### Revenue Sources (Per User/Week)

| Layer | Type | Effort | Weekly Revenue | Your Cut (30%) |
|-------|------|--------|----------------|----------------|
| Bandwidth Sharing | Truly passive | Zero | R5-10 | R1.50-3 |
| Data Marketplace | Passive (opt-in) | Zero | R10-20 | R3-6 |
| Offerwalls | Light active | 10-15 min | R15-25 | R4.50-7.50 |
| Micro-tasks | Active | 15-20 min | R20-40 | R6-12 |
| Gamification | Engagement glue | Built-in | R5-10 (bonus) | R1.50-3 |
| Referrals | Social | One-time | R5-15 ongoing | R1.50-4.50 |
| **Total** | | **~30-45 min/week** | **R60-120/week** | **R18-36/week** |

### Advertising Economics (SA Market)
- **Mobile ad RPM:** $0.50-1.50 (R9-27 per 1,000 impressions)
- **Facebook CPI (SA):** $1.26-7.57 (R23-137 per app install)
- **Offerwall CPA:** $1.50-5.00 per completed action
- **Survey completion:** $0.50-2.00 per survey

### Unit Economics at Scale

| Users | Weekly User Payouts | Your Weekly Revenue (30%) | Monthly Profit |
|-------|---------------------|---------------------------|----------------|
| 1,000 | R50,000 | R21,400 | R85,600 |
| 10,000 | R500,000 | R214,000 | R856,000 |
| 50,000 | R2,500,000 | R1,070,000 | R4,280,000 |

---

## Technical Architecture

### Proposed Stack
```
┌─────────────────────────────────────────────┐
│              Next.js Web App (PWA)           │
│         (works offline, no app store)        │
├─────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ Earn Hub │ │ Game/    │ │  Wallet &    │ │
│  │ (Tasks)  │ │ Compete  │ │  Cashout     │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
├─────────────────────────────────────────────┤
│         AI Task Routing Engine               │
│   (matches users → highest-paying tasks)     │
├─────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │
│  │Offerwall│ │Surveys │ │AI Tasks│ │Data  │ │
│  │Networks │ │Partners│ │Partners│ │Buyers│ │
│  └────────┘ └────────┘ └────────┘ └──────┘ │
├─────────────────────────────────────────────┤
│  Supabase (Auth, DB, Realtime)              │
│  + Fraud Detection + Payout Engine          │
└─────────────────────────────────────────────┘
```

### Key Technical Decisions
- **PWA over native app:** Avoids app store fees, instant updates, works on any device
- **Supabase backend:** Auth, database, realtime updates, edge functions
- **Multi-network offerwall aggregation:** Always have tasks available
- **Built-in fraud detection:** Protect margins from bots and abuse

### Offerwall Networks to Integrate
1. **IronSource** — Gaming offers, high payouts
2. **Tapjoy** — App installs, surveys
3. **AdGate Media** — Surveys, videos, signups
4. **OfferToro** — Diverse offers
5. **Pollfish** — Surveys (reliable)

### Survey Partners
- Pollfish
- Cint
- Theoremreach

### AI Task Partners
- Toloka (Yandex)
- Scale AI
- Appen
- Remotasks API

---

## How the Cut Works

### Revenue Flow
```
Advertiser pays:       R18.00  (to install their app)
    ↓
Offerwall network:     R3.60   (20% network fee)
    ↓
Platform receives:     R14.40  
    ↓
User receives:         R10.00  (what user sees)
    ↓
Platform keeps:        R4.40   (30% margin)
```

**Users never see the full payout amount — only their reward.**

### Recommended Cut by Layer
| Layer | Your Cut | Reasoning |
|-------|----------|-----------|
| Offerwalls | 25-30% | Industry standard |
| Surveys | 25-30% | Competitive |
| Video ads | 30-35% | Low effort for user |
| AI tasks | 25-30% | Active work |
| Bandwidth | 40-50% | Zero user effort |
| Data marketplace | 50% | You aggregate and package |

---

## Critical Problems & Solutions

### Problem 1: Payment Timing (Cash Flow)
**Issue:** Networks pay 30-60 days after task completion. Users expect faster.

**Solution:** Weekly payout cycle
- Users earn Mon-Sun, paid every Tuesday
- Transparent messaging: "Earn all week, get paid every Tuesday"
- Need R30-100k working capital to bridge first 8 weeks

### Problem 2: Task Availability
**Issue:** Single offerwall runs out of tasks quickly.

**Solution:** Multi-layer task system
1. Multiple offerwall networks (4-5 integrated)
2. Daily refresh tasks (guaranteed R10-15/day)
3. AI task pool (unlimited inventory)
4. Geographic rotation (location-specific offers)

### Problem 3: Fraud
**Issue:** Bots, fake accounts, self-referrals destroy margins.

**Solution:** Multi-layer fraud detection
```javascript
function calculateFraudScore(user) {
  let score = 0;
  
  // Device signals
  if (multipleAccountsSameDevice) score += 30;
  if (usingVPN) score += 20;
  if (usingEmulator) score += 40;
  
  // Behavior signals
  if (completionSpeedTooFast) score += 25;
  if (roboticClickPattern) score += 35;
  
  // Network signals
  if (networkFlaggedFraud) score += 50;
  
  return score;
}

// Actions
if (fraudScore > 80) → BAN
if (fraudScore > 50) → HOLD_PAYOUT
if (fraudScore > 30) → LIMIT_EARNINGS
```

### Problem 4: User Retention (Churn Points)
| Wall | When | Solution |
|------|------|----------|
| Task drought | Day 3-7 | Multi-network aggregation |
| Payout threshold | Day 7-14 | R20 minimum (vs R150 competitors) |
| Payment delay | Day 14-21 | Weekly payouts + notifications |
| Boredom | Day 21-30 | Gamification (streaks, leaderboards, levels) |
| Trust erosion | Any time | Radical transparency, public payout ledger |

---

## Gamification System

### Core Mechanics
- **Daily streaks:** Miss a day, lose multiplier
- **Weekly challenges:** "Complete 5 tasks → R5 bonus"
- **Leaderboards:** Top earner in your city wins R100
- **Level system:** Unlock higher-paying tasks at levels 5, 10, 20
- **Lucky spin:** Random bonus after completing tasks
- **Achievement badges:** Milestones and bragging rights

### Why It Matters
- Users come for money, **stay for the game**
- Increases retention by 30-50%
- Higher retention = higher LTV = sustainable business

---

## Financial Requirements

### Minimum Viable Launch (100 users)
- Working capital for payouts: **R20,000**
- Buffer for delays: **R10,000**
- **Total: R30,000**

### Scale Launch (500-1,000 users)
- Working capital: **R100,000-150,000**
- Marketing (optional): R10,000-20,000
- **Total: R110,000-170,000**

### Why Capital is Non-Negotiable
```
Week 1: Pay R10k (100 users) — you fund this
Week 2: Pay R20k — you fund this
Week 3: Pay R30k — you fund this
Week 4: Pay R40k — you fund this
...
Week 8: First network payment arrives (~R80k)
Week 12+: Self-sustaining (networks pay you R200k, you pay users R140k)
```

**Without R30-100k upfront, users won't get paid, they'll leave, and the app dies.**

---

## Phased Rollout Plan

### Phase 1: MVP (Month 1-3) — Budget: R100-200k
- PWA with offerwall aggregation + basic gamification
- Manual task curation
- 1,000 beta users via WhatsApp
- Target: R15-25/week per user
- **Goal: Validate retention and payout economics**

### Phase 2: Scale (Month 4-8) — Budget: R500k-1M
- Add bandwidth sharing + data marketplace
- AI task routing
- Referral engine
- WhatsApp viral campaign
- Target: 10,000 users, R40-60/week per user

### Phase 3: Dominate (Month 9-18) — Budget: R2-5M
- Direct advertiser deals
- AI training task partnerships
- City-by-city leaderboards
- SA brand partnerships
- Target: 50,000+ users, R60-100/week for power users

---

## Competitive Advantages (If Built)

| Competitor Problem | Our Solution |
|---|---|
| Low task availability | Multi-network aggregation |
| High withdrawal thresholds | R20 minimum |
| Slow payments | Weekly payouts (Tuesday) |
| No passive income | Bandwidth + data = R15-30/week passive |
| Users don't know what to do | AI routes best task automatically |
| Boring, no retention | Full gamification layer |
| No SA-specific opportunity | AI training in SA languages |
| Poor transparency | Real-time earnings dashboard |

---

## Zero-Capital Alternatives Considered

| Idea | Why It Fails |
|---|---|
| Only pay when networks pay | 60+ day wait = users leave, call it scam |
| Points/vouchers instead of cash | Still need to buy vouchers |
| Higher threshold (R500) | Users never reach it, churn |
| Partner with brands for rewards | Brands won't partner with zero users |
| Crowdfund the reserve | Need existing audience |
| Revenue share (no upfront) | "Paid in 60 days" = no signups |

**Conclusion: There is no viable zero-capital path for this business model.**

---

## Final Recommendation

### If You Have R30-100k
✅ Build it. The model works, market is underserved, I can build the tech.

### If You Have R0
❌ Don't build this now. Options:
1. **Save R30-50k first** (3-6 months)
2. **Find a partner with capital**
3. **Build something else** that doesn't require float capital
4. **Build a portfolio version** (no real payouts) to attract investors

---

## Alternative Project Ideas (No Capital Required)

### Option A: Build This as a Portfolio Project
- Full app without real payouts
- Use to attract investors or partners
- Demonstrates technical capability

### Option B: Different App (You Keep 100%)
- Utility app with ads (no user payouts)
- SaaS tool for SA market
- Content/community app with sponsorships

### Option C: Freelance First
- Build dev skills
- Earn capital through freelancing
- Return to this project with funding

---

## Resources & Links

### Offerwall Networks (Self-Serve Signup)
- IronSource: https://www.is.com/
- Tapjoy: https://www.tapjoy.com/
- AdGate Media: https://adgatemedia.com/
- OfferToro: https://www.offertoro.com/

### Survey Platforms
- Pollfish: https://www.pollfish.com/
- Cint: https://www.cint.com/

### AI Task Platforms
- Toloka: https://toloka.ai/
- Scale AI: https://scale.com/
- Appen: https://appen.com/

### Bandwidth Sharing (Reference)
- Pawns.app: https://pawns.app/
- PacketStream: https://packetstream.io/
- Bright Data SDK: https://brightdata.com/

---

## Next Steps (When Ready)

1. Secure R30-100k working capital
2. Switch to Code mode in Cascade
3. Build Phase 1 MVP (4-6 weeks)
4. Sign up for offerwall networks
5. Beta launch with 100-500 users
6. Iterate based on feedback
7. Scale via WhatsApp viral loops

---

*Document saved for future reference. Revisit when capital is available.*
