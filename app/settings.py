from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    jwt_secret: str = "dev-secret"
    jwt_expires_min: int = 60

    ollama_base_url: str = "http://localhost:11434"
    images_base_url: str = "http://localhost:8188"

    ai_text_default: str = "llama3.1:8b"
    ai_text_screenwriter: str = "qwen2.5:32b"
    ai_text_scene_default: str = "openhermes:7b"
    ai_text_scene_creative: str = "mythomax:13b"

    ai_image_fast: str = "sdxl-turbo"
    ai_image_quality: str = "sdxl"

    ai_max_tokens: int = 1024
    ai_temperature: float = 0.8

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
