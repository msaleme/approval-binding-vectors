"""Adversarial probe of the Verifiable Intent reference verifier (v0.1.0, commit 356c296).

Each case builds a valid autonomous chain, changes one thing (per VI security-model §4),
and records what verify_chain / check_constraints decide.

Two call profiles per case:
  default  - the call shape used in the repo's own integration tests
             (issuer key + serialized layers; no expected aud/nonce)
  hardened - default plus expected_l3_* aud/nonce and expected_l2 aud/nonce
"""
from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "examples"))

from helpers import (ACCEPTABLE_ITEMS, MERCHANTS, PAYMENT_INSTRUMENT,  # noqa: E402
                     checkout_hash_from_jwt, create_checkout_jwt, get_agent_keys,
                     get_issuer_keys, get_merchant_keys, get_user_keys)
from verifiable_intent import (AllowedMerchantConstraint, CheckoutL3Mandate,  # noqa: E402
                               CheckoutLineItemsConstraint, CheckoutMandate,
                               FinalCheckoutMandate, FinalPaymentMandate, IssuerCredential,
                               MandateMode, PaymentAmountConstraint, PaymentL3Mandate,
                               PaymentMandate, UserMandate, create_layer1,
                               create_layer2_autonomous, create_layer3_checkout,
                               create_layer3_payment, verify_chain)
from verifiable_intent.crypto.disclosure import build_selective_presentation, hash_bytes  # noqa: E402
from verifiable_intent.crypto.sd_jwt import decode_sd_jwt  # noqa: E402
from verifiable_intent.verification.constraint_checker import check_constraints  # noqa: E402

NETWORK_AUD = "https://www.mastercard.com"
MERCHANT_AUD = "https://tennis-warehouse.com"


def _find(sd, pred):
    for s, v in zip(sd.disclosures, sd.disclosure_values):
        if pred(v[-1] if v else None):
            return s
    return None


def build(*, amount=27999, l3a_aud=NETWORK_AUD, l3a_nonce="n-l3a", l3a_exp_offset=300,
          l3a_iat_offset=0, checkout_items=None, pay_tx_override=None,
          payment_agent=None, l2_signer=None, max_amount=40000):
    issuer, user, agent, merchant = get_issuer_keys(), get_user_keys(), get_agent_keys(), get_merchant_keys()
    pay_agent = payment_agent or agent
    now = int(time.time())
    cred = IssuerCredential(iss=NETWORK_AUD, sub="cred", iat=now, exp=now + 365 * 86400,
                            aud="https://wallet.example.com", email="user@example.com",
                            pan_last_four="1234", scheme="Mastercard", cnf_jwk=user.public_jwk)
    l1 = create_layer1(cred, issuer.private_key)
    l1_ser = l1.serialize()
    cm = CheckoutMandate(vct="mandate.checkout.open.1", cnf_jwk=agent.public_jwk, cnf_kid="agent-key-1",
                         constraints=[AllowedMerchantConstraint(allowed=MERCHANTS),
                                      CheckoutLineItemsConstraint(items=[{"id": "line-item-1",
                                                                          "acceptable_items": ACCEPTABLE_ITEMS[:1],
                                                                          "quantity": 1}])])
    pm = PaymentMandate(vct="mandate.payment.open.1", cnf_jwk=pay_agent.public_jwk, cnf_kid="agent-key-1",
                        payment_instrument=PAYMENT_INSTRUMENT,
                        constraints=[PaymentAmountConstraint(currency="USD", min=10000, max=max_amount)])
    um = UserMandate(nonce="n-l2", aud="https://www.agent.com", iat=now, iss="https://wallet.example.com",
                     exp=now + 86400, mode=MandateMode.AUTONOMOUS, sd_hash=hash_bytes(l1_ser.encode("ascii")),
                     checkout_mandate=cm, payment_mandate=pm, merchants=MERCHANTS, acceptable_items=ACCEPTABLE_ITEMS)
    l2 = create_layer2_autonomous(um, (l2_signer or user).private_key)
    l2_ser = l2.serialize()
    l2_base = l2_ser.split("~")[0]
    pay_d = _find(l2, lambda v: isinstance(v, dict) and v.get("vct") == "mandate.payment.open.1")
    co_d = _find(l2, lambda v: isinstance(v, dict) and v.get("vct") == "mandate.checkout.open.1")
    mer_d = _find(l2, lambda v: isinstance(v, dict) and v.get("name") == "Tennis Warehouse")
    item_d = _find(l2, lambda v: isinstance(v, dict) and v.get("id") == "BAB86345")
    co_jwt = create_checkout_jwt(checkout_items or [{"sku": "BAB86345", "quantity": 1}], merchant)
    c_hash = checkout_hash_from_jwt(co_jwt)
    fp = FinalPaymentMandate(transaction_id=pay_tx_override or c_hash, payee=MERCHANTS[0],
                             payment_amount={"currency": "USD", "amount": amount},
                             payment_instrument=PAYMENT_INSTRUMENT)
    l3a = create_layer3_payment(PaymentL3Mandate(nonce=l3a_nonce, aud=l3a_aud, iat=now + l3a_iat_offset,
                                                 iss="https://agent.example.com", exp=now + l3a_exp_offset,
                                                 final_payment=fp, final_merchant=MERCHANTS[0]),
                                agent.private_key, l2_base, pay_d, mer_d)
    l3b = create_layer3_checkout(CheckoutL3Mandate(nonce="n-l3b", aud=MERCHANT_AUD, iat=now,
                                                   iss="https://agent.example.com", exp=now + 300,
                                                   final_checkout=FinalCheckoutMandate(checkout_jwt=co_jwt,
                                                                                       checkout_hash=c_hash)),
                                 agent.private_key, l2_base, co_d, item_d)
    return dict(l1=l1, l2=l2, l3a=l3a, l3b=l3b, l1_ser=l1_ser, l2_ser=l2_ser, issuer=issuer,
                l2_pay=build_selective_presentation(l2_base, [pay_d, mer_d]),
                l2_co=build_selective_presentation(l2_base, [co_d, item_d]), amount=amount,
                pm_constraints=[c.to_dict() if hasattr(c, "to_dict") else c for c in pm.constraints])


def verify(c, *, profile, l3a=None, l3b=None, payment_only=False, skew=300):
    kw = dict(issuer_public_key=c["issuer"].public_key, l1_serialized=c["l1_ser"], l2_serialized=c["l2_ser"],
              l2_payment_serialized=c["l2_pay"], l2_checkout_serialized=c["l2_co"], clock_skew_seconds=skew,
              l3_payment=l3a or c["l3a"], l3_checkout=None if payment_only else (l3b or c["l3b"]))
    if profile == "hardened":
        kw.update(expected_l2_aud="https://www.agent.com", expected_l2_nonce="n-l2",
                  expected_l3_payment_aud=NETWORK_AUD, expected_l3_payment_nonce="n-l3a")
        if not payment_only:
            kw.update(expected_l3_checkout_aud=MERCHANT_AUD, expected_l3_checkout_nonce="n-l3b")
    r = verify_chain(c["l1"], c["l2"], **kw)
    return r


def row(case, section, expect, c, harness, note="", **vkw):
    out = {"case": case, "vi_section": section, "spec_expectation": expect, "harness_candidates": harness, "note": note}
    for prof in ("default", "hardened"):
        r = verify(c, profile=prof, **vkw)
        out[prof] = {"valid": r.valid, "errors": r.errors[:3],
                     "skipped": [s for s in r.checks_skipped if any(k in s for k in ("aud", "nonce"))][:4]}
    return out


results = []

# P0 positive control
c = build()
results.append(row("P0 valid chain (positive control)", "-", "accept", c, "-"))

# 4.1 replay of the same L3a (stateless verifier)
c = build()
r1 = verify(c, profile="hardened", payment_only=True)
r2 = verify(c, profile="hardened", payment_only=True)
results.append({"case": "4.1 same L3a presented twice", "vi_section": "4.1",
                "spec_expectation": "verifier MUST reject a nonce already seen",
                "harness_candidates": "AP2-011, CTK-005",
                "note": "library keeps no nonce store; replay detection is the integrator's",
                "default": {"valid": [r1.valid, r2.valid]}, "hardened": {"valid": [r1.valid, r2.valid]}})

# 4.1 cross-merchant / wrong audience
c = build(l3a_aud="https://attacker-merchant.example")
results.append(row("4.1 L3a addressed to another audience", "4.1", "verifier MUST check aud", c, "CTK-002, MCP-022 (class)",
                   payment_only=True))

# 4.2 second L3a from the same L2 (new nonce)
c = build()
c2 = build(l3a_nonce="n-l3a-second")
results.append({"case": "4.2 N+1 L3a from one L2 mandate pair (fresh nonce)", "vi_section": "4.2",
                "spec_expectation": "payment network MUST track issuance per L2 (sd_hash) and reject",
                "harness_candidates": "AP2-013, CTK-004",
                "note": "by design outside the library; the network's stateful log is the control",
                "default": {"valid": [verify(c, profile="default", payment_only=True).valid,
                                      verify(c2, profile="default", payment_only=True).valid]},
                "hardened": {"valid": "n/a: each L3a carries its own nonce, so expected-nonce cannot bind it to one use"}})

# 4.2 amount above the L2 cap
c = build(amount=99999)
rr = row("4.2 L3a amount above L2 max (99,999 > 40,000)", "4.2 step 4 / constraints.md",
         "reject (amount_range)", c, "CTK-003", payment_only=True)
fp = json.loads(json.dumps(rr))
cc = check_constraints(c["pm_constraints"], {"payment_amount": {"currency": "USD", "amount": 99999}}, is_open_mandate=True)
rr["check_constraints"] = {"satisfied": cc.satisfied, "violations": cc.violations[:2]}
results.append(rr)

# 4.3 constraint stripping, modelled as an L2 signed by a non-user key
c = build(l2_signer=get_agent_keys())
results.append(row("4.3 L2 re-signed by attacker key (stripped constraints)", "4.3", "reject (L2 signature)", c,
                   "AP2-008 (adjacent: sd_hash substitution)"))

# 4.4 checkout-payment mismatch: payment refers to a different checkout
c = build(pay_tx_override="X" * 43)
results.append(row("4.4a mismatch, both L3s presented", "4.4", "reject (cross-reference)", c, "AP2-007"))
results.append(row("4.4b mismatch, network sees L3a only", "4.4", "spec: network cannot see checkout; relies on L2 conditional_transaction_id",
                   c, "AP2-007", payment_only=True))

# 4.5 alg confusion: alg=none, signature stripped
c = build()
ser = c["l3a"].serialize()
jwt, *rest = ser.split("~")
h, p, _sig = jwt.split(".")
hdr = json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
hdr["alg"] = "none"
h2 = base64.urlsafe_b64encode(json.dumps(hdr).encode()).decode().rstrip("=")
try:
    forged = decode_sd_jwt("~".join([f"{h2}.{p}."] + rest))
    results.append(row("4.5 L3a with alg=none, no signature", "4.5", "reject (ES256 only)", c, "MCP-022 (class), none direct",
                       l3a=forged, payment_only=True))
except Exception as e:  # parse-time rejection is also a rejection
    results.append({"case": "4.5 L3a with alg=none, no signature", "vi_section": "4.5", "spec_expectation": "reject",
                    "harness_candidates": "-", "default": {"valid": False, "errors": [f"parse: {e!s:.90}"]},
                    "hardened": {"valid": False}})

# 4.6 clock skew: L3a expired 200 s ago
c = build(l3a_iat_offset=-400, l3a_exp_offset=-200)
results.append(row("4.6 L3a expired 200 s ago (default skew 300 s)", "4.6", "RECOMMENDED tolerance; accepted by design",
                   c, "AP2-012, CTK-007", payment_only=True))
results.append(row("4.6 same, verifier skew 60 s", "4.6", "reject", c, "AP2-012, CTK-007", payment_only=True, skew=60))

# 4.9 split agent: payment mandate delegates a different agent key
from helpers import get_merchant_keys as _alt  # any distinct key pair
c = build(payment_agent=_alt())
results.append(row("4.9 checkout and payment mandates bind different agent keys", "4.9", "reject (cnf.jwk must match)", c,
                   "CTK-001"))

# 4.4c merchant sees only L3b; only L3a's transaction_id was changed (added after review)
c = build(pay_tx_override="X" * 43)
r_m = verify_chain(c["l1"], c["l2"], l3_checkout=c["l3b"], issuer_public_key=c["issuer"].public_key,
                   l1_serialized=c["l1_ser"], l2_serialized=c["l2_ser"], l2_payment_serialized=c["l2_pay"],
                   l2_checkout_serialized=c["l2_co"], expected_l3_checkout_aud=MERCHANT_AUD,
                   expected_l3_checkout_nonce="n-l3b")
results.append({"case": "4.4c mismatch, merchant sees L3b only", "vi_section": "4.4 / spec 8.4",
                "spec_expectation": "each party verifies its own L3; cross-reference only when one verifier holds both",
                "harness_candidates": "AP2-007", "note": "merchant-role call with expected aud/nonce",
                "default": {"valid": "n/a"}, "hardened": {"valid": r_m.valid, "errors": r_m.errors[:2]}})

print(json.dumps({"vi_commit": "356c296", "python": sys.version.split()[0], "results": results}, indent=1, default=str))
