import secrets


def generate_job_token() -> str:
    """Generate an 8-char lowercase hex job token via cryptographically secure random.

    4 bytes = 32 bits of entropy. Adequate for MVP (tens of concurrent jobs).
    Production scale warrants increasing to secrets.token_hex(8) (64 bits).
    """
    return secrets.token_hex(4)
