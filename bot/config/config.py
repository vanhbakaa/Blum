from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str


    REF_LINK: str = ""


    AUTO_TASK: bool = True
    AUTO_GAME: bool = True
    GAME_PLAY_EACH_ROUND: list[int] = [5, 10]
    MAX_POINTS: int = 220
    MIN_POINTS: int = 180

    DELAY_EACH_ACCOUNT: list[int] = [20, 30]

    ADVANCED_ANTI_DETECTION: bool = True

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()

