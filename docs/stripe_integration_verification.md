Comprehensive audit of my Stripe integration for a SaaS with subscriptions. Check ALL these points:

═══════════════════════════════════════
📊 1. STATUS & LIFECYCLE MANAGEMENT
═══════════════════════════════════════
- All statuses handled: active, past_due, incomplete, canceled, unpaid, trialing?
- Difference between "canceled" and "canceled_at_period_end" (immediate vs end of period)?
- Grace period: how many days after failure before cutting access?
- Essential webhooks listened to:
  * customer.subscription.created
  * customer.subscription.updated
  * customer.subscription.deleted
  * invoice.payment_failed
  * invoice.payment_succeeded
  * charge.refunded

═══════════════════════════════════════
💳 2. PAYMENTS & FAILURES
═══════════════════════════════════════
- stripe_customer_id saved and reused (no duplication)?
- Expired card handling (invoice.payment_action_required)?
- 3D Secure failures handled (requires_action)?
- Failed payment retry logic: how many attempts? Over how many days?
- Automatic email sent after payment failure?
- Dedicated table for logging refunds (avoid inconsistencies)?

═══════════════════════════════════════
🔐 3. SECURITY & IDEMPOTENCY
═══════════════════════════════════════
- Webhook signature verified with stripe.Webhook.construct_event()?
- Event IDs stored to prevent duplicate processing?
- Webhook endpoint protected (no classic auth, but signature)?
- Webhook timeout < 30s (otherwise Stripe retries)?
- 200 OK response even if processing fails (to avoid infinite retries)?
- Webhooks can arrive out of order: processing order guaranteed?

═══════════════════════════════════════
💰 4. UPGRADES / DOWNGRADES
═══════════════════════════════════════
- Proration handled during plan changes?
- Proration_behavior defined (create_prorations, always_invoice, none)?
- Quota immediately updated after upgrade?
- What happens if downgrade and quota already exceeded?

═══════════════════════════════════════
🎟️ 5. COUPONS & PROMOTIONS
═══════════════════════════════════════
- Support for Stripe coupons (percent_off, amount_off)?
- Limited coupon duration respected (once, repeating, forever)?
- Coupon validity check before application?
- Discount displayed in user interface?

═══════════════════════════════════════
🌍 6. TAXES & INTERNATIONAL
═══════════════════════════════════════
- European VAT handled (Stripe Tax enabled or manual calculation)?
- Billing address requested?
- Multiple currencies supported or EUR only?

═══════════════════════════════════════
⚠️ 7. CRITICAL EDGE CASES
═══════════════════════════════════════
- Double-click during checkout (duplicated session)?
- User cancels mid-checkout: expired session handled?
- Disputed payment (chargeback): charge.dispute.created event listened?
- User deletes account but has active subscription?
- Stripe customer deleted but user still exists in DB?
- What happens if webhook never arrives (manual backup check)?

═══════════════════════════════════════
📧 8. USER NOTIFICATIONS
═══════════════════════════════════════
- Email after successful subscription?
- Email before renewal (3 days before)?
- Email after payment failure?
- Email after cancellation?
- Invoice email (or use native Stripe emails)?

═══════════════════════════════════════
📊 9. LOGS & MONITORING
═══════════════════════════════════════
- ALL payment events logged (stripe_events table)?
- Logs include: event_id, type, created, processed_at, error?
- Monitoring alerts if:
  * Webhook fails 3+ times?
  * Payment failure rate > 5%?
  * Customer portal inaccessible?

═══════════════════════════════════════
🧪 10. TESTS & SCENARIOS
═══════════════════════════════════════
Tests covered for:
- Valid card → success
- Declined card (4000000000000002)
- 3D Secure required (4000002500003155)
- Expired card (4000000000000069)
- Insufficient funds (4000000000009995)
- Immediate cancellation
- End-of-period cancellation
- Mid-cycle upgrade
- Mid-cycle downgrade
- Full refund
- Partial refund
- Webhook arrives 2x (idempotency)
- Webhook arrives out of order

═══════════════════════════════════════
🚀 11. PRODUCTION READINESS
═══════════════════════════════════════
- Stripe currently in TEST mode?
- Migration plan to LIVE mode documented?
- Production webhook URL configured in Stripe dashboard?
- API keys stored in environment variables (not hardcoded)?
- Rate limiting on checkout endpoints (prevent spam)?
- Stripe customer portal configured and customized?

═══════════════════════════════════════

For each missing point, provide:
1. The risk involved
2. The correction to apply (concise)
3. Priority (P0=blocking, P1=important, P2=nice-to-have)