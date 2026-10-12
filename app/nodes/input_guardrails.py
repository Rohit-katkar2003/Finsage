from __future__ import annotations
from ..schemas import AgentState 
    #!/usr/bin/env python3
"""
Production-ready input guardrails for LLM agents.

Layers:
  1. Sanitization    -> Unicode normalization + zero-width stripping
  2. Regex filters   -> structured PII, secrets, and hard length limits
  3. Luhn validation -> eliminates credit-card false positives
  4. Prompt injection-> regex blocklist on de-obfuscated text
  5. Decision        -> block / redact / allow

Zero external dependencies. Python 3.9+.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

# =====================================================================
# 1. SANITIZATION
# =====================================================================

# Zero-width and bidi control characters used to hide payloads
_ZERO_WIDTH = re.compile(
    r"[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff\u00ad]"
)
_WS_COLLAPSE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """NFKC-normalize and strip zero-width / bidi control characters."""
    t = unicodedata.normalize("NFKC", text)
    return _ZERO_WIDTH.sub("", t)


def deobfuscate(text: str) -> str:
    """
    Lowercase and collapse everything that is not [a-z0-9] into a single
    space. This defeats obfuscation like 'i.g.n.o.r.e' or 'I G N O R E'.
    Only used for injection matching (spans are not needed there).
    """
    t = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return _WS_COLLAPSE.sub(" ", t).strip()


# =====================================================================
# 2. REGEX PATTERN SETS
# =====================================================================

# ---- 2a. PII -------------------------------------------------------

PII_PATTERNS: dict[str, str] = {
    "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "PHONE_US": r"(?<!\d)(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?!\d)",
    "PHONE_INTL": r"(?<!\d)\+\d{1,3}[\s.\-]?\d{2,4}[\s.\-]?\d{2,4}[\s.\-]?\d{2,4}(?!\d)",
    "SSN_US": r"(?<!\d)\d{3}[\s\-]\d{2}[\s\-]\d{4}(?!\d)",
    "CREDIT_CARD": r"(?<!\d)(?:\d[ \-]?){13,19}(?!\d)",
    "IBAN": r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}[ ]?[A-Z0-9]{1,4}\b",
    "AADHAAR_IN": r"(?<!\d)[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)",
    "PAN_IN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "IPV4": r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
    "IPV6": r"\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b",
    "MAC": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
    "DOB": r"\b(?:0?[1-9]|1[0-2])[/\-](?:0?[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b",
}

# ---- 2b. Secrets / credentials ------------------------------------

SECRET_PATTERNS: dict[str, str] = {
    "OPENAI_KEY": r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b",
    "ANTHROPIC_KEY": r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b",
    "AWS_ACCESS_KEY": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "GITHUB_TOKEN": r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
    "SLACK_TOKEN": r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b",
    "GOOGLE_API_KEY": r"\bAIza[0-9A-Za-z_\-]{35}\b",
    "STRIPE_KEY": r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{20,}\b",
    "JWT": r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b",
    "PRIVATE_KEY_BLOCK": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----",
    "BEARER_TOKEN": r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]{20,}=*\b",
}

# ---- 2c. Prompt injection -----------------------------------------
# Applied to de-obfuscated text, so patterns are plain lowercase words
# with \W+ between tokens to tolerate arbitrary separators.

# ---------------------------------------------------------------------
# Patterns are written against the COMPACT form (no spaces, no symbols).
# Use \w{0,N} to allow filler words between key tokens.
# ---------------------------------------------------------------------
_RAW_INJECTION_PATTERNS: list[str] = [
    # --- instruction override ---------------------------------------
    r"ignore\w{0,40}(?:instructions?|rules?|prompts?|guidelines?)",
    r"disregard\w{0,40}(?:instructions?|rules?|prompts?|guidelines?)",
    r"forget\w{0,40}(?:instructions?|rules?|prompts?|everything|allyou)",
    r"override\w{0,40}(?:instructions?|rules?|guidelines?|polic(?:y|ies)|prompts?)",
    r"(?:new|updated|revised)\w{0,10}instructions",
    r"followmyinstructions",

    # --- role hijack / jailbreak ------------------------------------
    r"youarenow(?:a|an|the|dan|not)",
    r"actas\w{0,20}(?:unrestricted|unfiltered|jailbroken|evil|dan|admin|root)",
    r"pretend\w{0,20}(?:tobe|youare|thatyou)",
    r"doanythingnow",
    r"jailbreak",
    r"(?:enable|enter|activate|switchto)\w{0,20}(?:developer|debug|god|admin|unrestricted|dan)\w{0,10}mode",

    # --- system prompt / hidden instruction extraction ---------------
    r"(?:reveal|show|print|repeat|output|leak|expose|dump|give)\w{0,40}"
    r"(?:system|initial|hidden|original|secret|developer|your)\w{0,20}"
    r"(?:prompt|instructions?|rules?|keys?|message)",
    r"(?:system|initial|hidden|original|developer)\w{0,10}(?:prompt|instructions?|message)",
    r"whatareyour\w{0,20}(?:instructions?|rules?|prompt)",
    r"repeat\w{0,20}(?:words?|text|prompt|above)",

    # --- credentials / exfil ----------------------------------------
    r"(?:give|show|send|reveal|leak)\w{0,20}api\w{0,5}keys?",
    r"(?:send|post|upload|exfiltrate|forward|curl|wget)\w{0,40}https?",

    # --- control tokens (become plain text after compacting) ----------
    r"imstart|imend|endoftext",
    r"inst\b",           # [INST]
    r"sys\b",            # <<SYS>>
    r"beginsystemprompt",
]

INJECTION_PATTERNS: dict[str, re.Pattern] = {
    f"INJ_{i:02d}": re.compile(p)
    for i, p in enumerate(_RAW_INJECTION_PATTERNS)
}
# Compiled PII / secret patterns
_COMPILED_PII = {
    name: re.compile(p, re.IGNORECASE) for name, p in PII_PATTERNS.items()
}
_COMPILED_SECRETS = {
    name: re.compile(p) for name, p in SECRET_PATTERNS.items()
}

# =====================================================================
# 3. VALIDATORS
# =====================================================================


def luhn_ok(number: str) -> bool:
    """Luhn checksum — removes most credit-card false positives."""
    digits = [int(c) for c in re.sub(r"\D", "", number)]
    if not (12 <= len(digits) <= 19):
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def is_valid_aadhaar(number: str) -> bool:
    """Aadhaar uses Verhoeff checksum; we only enforce the format guard."""
    digits = re.sub(r"\D", "", number)
    return len(digits) == 12 and digits[0] in "23456789"


# =====================================================================
# 4. DATA TYPES
# =====================================================================

Action = Literal["allow", "redact", "block"]


@dataclass
class Finding:
    category: str          # "PII" | "SECRET" | "INJECTION"
    type: str              # e.g. "EMAIL", "INJ_03"
    value: str             # matched text (empty for injection)
    span: tuple[int, int]  # (start, end) in normalized text; (-1,-1) if N/A


@dataclass
class GuardrailResult:
    allowed: bool
    action: Action
    reason: str = ""
    findings: list[Finding] = field(default_factory=list)
    sanitized_text: str = ""

    def __bool__(self) -> bool:
        return self.allowed


# =====================================================================
# 5. THE GUARDRAIL
# =====================================================================


class InputGuardrail:
    """
    Layered input guardrail for LLM agents.

    Parameters
    ----------
    max_chars : int
        Hard cap on input length (after normalization).
    block_on_pii : bool
        True  -> any PII match blocks the request.
        False -> PII is redacted and the request continues.
    block_on_secrets : bool
        Always recommended True.
    block_on_injection : bool
        True  -> injection pattern blocks.
    redact_token : str
        Placeholder format, e.g. "<EMAIL>".
    """

    def __init__(
        self,
        max_chars: int = 4096,
        block_on_pii: bool = True,
        block_on_secrets: bool = True,
        block_on_injection: bool = True,
        redact_token: str = "<{type}>",
    ) -> None:
        self.max_chars = max_chars
        self.block_on_pii = block_on_pii
        self.block_on_secrets = block_on_secrets
        self.block_on_injection = block_on_injection
        self.redact_token = redact_token

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------
    def scan(self, text: str) -> GuardrailResult:
        if not isinstance(text, str):
            return GuardrailResult(False, "block", "Input must be a string")

        clean = normalize(text)

        # --- Layer 0: length -----------------------------------------
        if len(clean) > self.max_chars:
            return GuardrailResult(
                allowed=False,
                action="block",
                reason=f"Input exceeds {self.max_chars} characters",
                sanitized_text=clean[: self.max_chars],
            )

        findings: list[Finding] = []

        # --- Layer 1: prompt injection (on de-obfuscated text) -------
        def compact(text: str) -> str:
            return re.sub(r"[^a-z0-9]", "", text.lower())
        deob = compact(clean)
        for name, pattern in INJECTION_PATTERNS.items():
            if pattern.search(deob):
                findings.append(
                    Finding("INJECTION", name, "", (-1, -1))
                )

        if findings and self.block_on_injection:
            return GuardrailResult(
                False,
                "block",
                "Prompt injection detected",
                findings,
                clean,
            )

        # --- Layer 2: secrets ----------------------------------------
        for name, pattern in _COMPILED_SECRETS.items():
            for m in pattern.finditer(clean):
                findings.append(
                    Finding("SECRET", name, m.group(), m.span())
                )

        if any(f.category == "SECRET" for f in findings) and self.block_on_secrets:
            return GuardrailResult(
                False, "block", "Secret/credential detected", findings, clean
            )

        # --- Layer 3: PII --------------------------------------------
        for name, pattern in _COMPILED_PII.items():
            for m in pattern.finditer(clean):
                value = m.group()

                # False-positive guards
                if name == "CREDIT_CARD" and not luhn_ok(value):
                    continue
                if name == "AADHAAR_IN" and not is_valid_aadhaar(value):
                    continue
                if name == "PHONE_US" and len(re.sub(r"\D", "", value)) < 10:
                    continue
                # Don't re-flag IP fragments inside IPv6
                if name == "IPV4" and ":" in clean[max(0, m.start() - 1): m.start()]:
                    continue

                findings.append(
                    Finding("PII", name, value, m.span())
                )

        pii_findings = [f for f in findings if f.category == "PII"]

        if pii_findings and self.block_on_pii:
            return GuardrailResult(
                False, "block", "PII detected", findings, clean
            )

        # --- Decision ------------------------------------------------
        if findings:
            return GuardrailResult(
                True,
                "redact",
                "Sensitive data redacted",
                findings,
                self._redact(clean, findings),
            )

        return GuardrailResult(True, "allow", "", [], clean)

    def redact(self, text: str) -> str:
        """Convenience: always returns redacted text (never blocks)."""
        res = self.scan(text)
        return res.sanitized_text

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------
    def _redact(self, text: str, findings: list[Finding]) -> str:
        """Replace non-overlapping spans right-to-left."""
        spans = [
            (f.span[0], f.span[1], f.type)
            for f in findings
            if f.span[0] >= 0 and f.value
        ]
        # Sort descending by start; skip overlaps
        spans.sort(key=lambda s: s[0], reverse=True)
        out = text
        last_start = len(text) + 1
        for start, end, ftype in spans:
            if end > last_start:
                continue
            out = out[:start] + self.redact_token.format(type=ftype) + out[end:]
            last_start = start
        return out


# =====================================================================
# 6. DEMO / SELF-TEST
# =====================================================================


import time 

def InputGuardrailNode(state: AgentState):
    guard = InputGuardrail(
        max_chars=4096,
        block_on_pii=False,       # redact PII instead of blocking
        block_on_secrets=True,
        block_on_injection=True,
    )

    raw = state.get("input_query", "") or ""
    result = guard.scan(raw)

    if not result.allowed:
        return {
            "blocked": True,
            "block_reason": result.reason or "guardrail",
            "query": "",
            "started_at": time.time(),
            "trace": [{"node": "input_guardrails", "t": time.time(),
                       "action": "block", "reason": result.reason}],
        }

    clean = result.sanitized_text or raw
    return {
        "blocked": False,
        "query": clean,
        "retries": 0,
        "started_at": time.time(),
        "trace": [{"node": "input_guardrails", "t": time.time(),
                   "action": result.action,
                   "findings": [f.type for f in result.findings]}],
    }