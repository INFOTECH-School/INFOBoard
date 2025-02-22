from draw import settings


def version(request):
    return {'VERSION': settings.SOFT_VERSION}
