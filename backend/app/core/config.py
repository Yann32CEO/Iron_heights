from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Iron Heights V2 API"
    app_env: str = "development"
    app_port: int = 8086
    database_url: str
    jwt_secret: str
    phase3_jwt_secret: str = ""
    phase3_aes_password: str
    cors_allow_origins: str
    artemis_ollama_enabled: bool = True
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5:0.5b-instruct"
    ollama_timeout_ms: int = 6000
    # Challenge services must read flags from settings at award time so env overrides stay authoritative.
    flag_phase1_cell: str
    flag_phase1_uniform: str
    flag_phase2_director: str
    flag_phase3_relay: str
    flag_phase3_roof: str
    flag_final: str

    @property
    def phase3_signing_secret(self) -> str:
        # Phase 3's encrypted intercept must reveal the same HS256 secret the relay verifier trusts.
        return self.phase3_jwt_secret or self.jwt_secret

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
