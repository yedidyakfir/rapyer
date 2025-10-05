from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="REDIS_PYDANTIC",
    settings_files=["settings.toml", ".secrets.toml"],
    environments=True,
    load_dotenv=True,
)
