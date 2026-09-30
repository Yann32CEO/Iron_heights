# Shared AES-256-GCM key leaked by /internal/tr4nsf3r/e-scrow. Every session's cell lock is sealed with it,
# so the key alone is useless without the player's own ciphertext, IV and auth tag.
PHASE1_ESCROW_KEY_HEX = "5d1eb65185d419956edc1886ddc74bccaa8625a921050713d2c3d79985565c91"

PHASE1_CELL_CODE_LENGTH = 14
