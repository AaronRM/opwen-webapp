from ca.ascoderu.lokole.domain.config import OpwenConfig
from ca.ascoderu.lokole.domain.email.base64 import Base64AttachmentEncoder
from ca.ascoderu.lokole.domain.email.memory import InMemoryEmailStore
from ca.ascoderu.lokole.domain.sync.azure import AzureSync
from ca.ascoderu.lokole.infrastructure.serialization.json import JsonSerializer


class Ioc(object):
    email_store = InMemoryEmailStore()

    email_sync = AzureSync(
        account_name=OpwenConfig.STORAGE_ACCOUNT_NAME,
        account_key=OpwenConfig.STORAGE_ACCOUNT_KEY,
        container=OpwenConfig.STORAGE_CONTAINER,
        download_location=OpwenConfig.STORAGE_DOWNLOAD_PATH,
        upload_location=OpwenConfig.STORAGE_UPLOAD_PATH,
        serializer=JsonSerializer())

    attachment_encoder = Base64AttachmentEncoder()
