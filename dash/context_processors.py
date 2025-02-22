from draw import settings


def version(request):
    return {'VERSION': settings.SOFT_VERSION}

def year(request):
    return {'YEAR': settings.NOW_YEAR}
