import mimetypes
import tempfile
import threading

import django.conf
import django.core.files.base
import django.core.files.storage
import django.utils.deconstruct

import google.cloud.storage
import google.cloud.storage.client


def get_storage_settings():
    config = getattr(django.conf.settings, "DJANGO_GCLOUD_STORAGE", {})

    # How much memory should be used before the temp file is written to disk.
    # 0 means don't ever write to disk
    config.setdefault('MAX_MEMORY_SIZE', 0)
    config.setdefault('DEFAULT_CONTENT_TYPE', 'application/octet-stream')

    return config


class GCloudStorage(django.core.files.storage.Storage):

    config = get_storage_settings()

    def __init__(self):
        self.thread = threading.local()

    @property
    def client(self):
        if not hasattr(self.thread, "client"):
            project = self.config.get('PROJECT')
            credentials = self.config.get('CREDENTIALS')
            self.thread.client = google.cloud.storage.client.Client(
                project=project,
                credentials=credentials)

        return self.thread.client

    def _open(self, name, mode):
        if 'w' in mode:
            raise ValueError("Writing to GCloud storage is not supported")
        blob = self._get_blob(name=name)

        file_obj = tempfile.SpooledTemporaryFile(mode="w+b")
        blob.download_to_file(file_obj)
        file_obj.flush()
        file_obj.seek(0)

        return django.core.files.base.File(file_obj)

    def _save(self, name, content):
        """
        Saves the fiven content to the given path. The name is already verified,
        so we're ready to go.

        `content` is a django FileField already, which contains the actual
        UploadedFile.
        """
        blob = self._get_blob(name=name)
        blob.upload_from_file(
            file_obj=content,
            rewind=True,
            size=content.size,
            content_type=self._guess_content_type(name=name, content=content))
        return name

    def delete(self, name):
        blob = self._get_blob(name=name)
        blob.delete()

    def exists(self, name):
        blob = self._get_blob(name=name)
        return blob.exists()

    def size(self, name):
        blob = self._get_blob(name=name)
        blob.reload()
        return blob.size

    def url(self, name):
        """
        Gets the public URL of the file.

        There are different valid URLs for a single file. Take a peek here:

            https://cloud.google.com/storage/docs/xml-api/reference-uris

        Essentially, these two:

            storage.googleapis.com/<bucket>/[<object>]
            <bucket>.storage.googleapis.com/[<object>]

        Now, the blob API's `public_url` will get us the first one. But,
        in order to better work with thumbnailing services, we'd want the
        second one.

        Also, we ideally don't want this to hit the API at all (for speed),
        so we just construct the URL ourselves.
        """
        return (
            "https://{bucket_name}.storage.googleapis.com/{path}"
            .format(
                bucket_name=self.config.get('BUCKET'),
                path=name))

    def created_time(self, name):
        pass

    def modified_time(self, name):
        pass

    # def get_available_name(self, name, max_length=None):
    #     pass

    def _get_blob(self, name):
        """
        Gets the blob instance for a given path.

        This doesn't hit the API yet.
        """
        # name = self._normalize_name(name)
        bucket = self.client.get_bucket(self.config.get('BUCKET'))
        return google.cloud.storage.Blob(name, bucket)

    def _guess_content_type(self, name, content):
        """
        Tries to guess the content type from the file's content and name.
        `content` is a django FileField.
        """
        # Try to guess from the FileField itself. Django usually supplies
        # the mime type in a InMemoryUploadedFile or UploadedFile, so we just
        # have to get there if possible.
        type_from_content = getattr(content, 'content_type', None)
        if not type_from_content:
            uploaded_file = getattr(content, 'file', None)
            if uploaded_file:
                type_from_content = getattr(uploaded_file, 'content_type', None)

        # Fallback #1: get the mimetype from the filename
        type_from_name, _ = mimetypes.guess_type(name)

        # Fallback #2: Use the default one
        default_type = self.config['DEFAULT_CONTENT_TYPE']

        return type_from_content or type_from_name or default_type
