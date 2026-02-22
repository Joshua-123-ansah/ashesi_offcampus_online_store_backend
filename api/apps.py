from django.apps import AppConfig


def _patch_django_context_py314():
    """
    Fix Django 4.2 BaseContext.__copy__ on Python 3.14.
    copy(super()) no longer returns an object that accepts new attributes.
    Copy all instance attributes so Context/RequestContext keep template,
    render_context, request, etc.
    """
    import django.template.context as ctx_mod
    base = ctx_mod.BaseContext

    def __copy__(self):
        duplicate = object.__new__(type(self))
        duplicate.dicts = self.dicts[:]
        for key, value in self.__dict__.items():
            if key != "dicts":
                setattr(duplicate, key, value)
        return duplicate

    base.__copy__ = __copy__


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        import sys
        if sys.version_info >= (3, 14):
            _patch_django_context_py314()
